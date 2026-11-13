"""Memory Extractor：从对话中提取候选记忆

只负责识别，不直接写数据库。写库由 Manager 负责。
输入：一批对话（含 message_id 供追溯）+ user_id
输出：候选记忆列表，每条含 category/memory_key/memory_value/confidence/evidence/source_message_ids/expression_type/memory_action

特别注意（Prompt 强约束）：
- 询问某枪 ≠ 喜欢这把枪，不要提取为偏好
- 试用一次 ≠ 长期偏好
- 说"不错"不一定代表以后都偏好
- 明确说"以后不用"才触发偏好更新
- 不确定的内容不能成为高置信度长期记忆
"""
import json
import re

from openai import OpenAI

from config.settings import settings

# ===== LLM 客户端（复用 DeepSeek）=====
_extract_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

# ===== 提取 Prompt =====
EXTRACT_PROMPT = """你是玩家记忆提取器。从下面这批三角洲行动游戏助手对话中，提取玩家的长期偏好和习惯记忆。

## 提取规则（严格遵守）
1. 只提取长期偏好/习惯，不提取临时询问或一次性查询
2. 玩家询问某把枪 ≠ 喜欢这把枪，不要提取为偏好
3. 玩家试用一次某把枪 ≠ 长期偏好，expression_type 标为 temporary
4. 玩家说"这把枪不错"但没说以后要用，不要轻易提取为高置信度偏好
5. 玩家明确说"以后不再使用这把枪"或"我喜欢低后坐力"这种明确表达，才标 explicit 高置信度
6. 多次表现出相同选择倾向，标 repeated_behavior
7. 根据行为推断的（没明说），标 inferred，置信度不超过 0.5
8. 不确定的内容不能成为高置信度长期记忆，置信度不超过 0.3
9. 游戏数据（价格/伤害/射速等客观数据）不是玩家记忆，不要提取

## 支持的记忆类别和 Key 命名空间
- weapon: weapon.preferred_type(枪械类型偏好) / weapon.price_range(价格偏好) / weapon.damage_preference(伤害偏好) / weapon.recoil_preference(后坐力偏好) / weapon.fire_rate_preference(射速偏好)
- map: map.preferred(喜欢的地图) / map.disliked(不喜欢的地图)
- ammo: ammo.preferred_type(弹药偏好)
- combat: combat.preferred_range(交战距离偏好) / combat.play_style(战斗风格) / combat.tactical_preference(战术偏好)
允许扩展新 Key，但必须符合 category.sub_key 的命名规范（全小写+下划线）

## 每条候选记忆必须包含
- category: weapon/map/ammo/combat 之一
- memory_key: 上面的命名空间之一或符合规范的新键
- memory_value: {"preference":"偏好值","description":"说明"} 格式
- confidence: 0.0-1.0，按表达类型和确定性评估（explicit 0.6-0.9，repeated 0.5-0.8，inferred 0.2-0.5，temporary 0.1-0.3）
- evidence: 这条记忆的依据（引用对话中的原话或行为）
- source_message_ids: 这条记忆来自哪些消息id（数组）
- expression_type: explicit/repeated_behavior/inferred/temporary 之一
- memory_action: create(创建新记忆)/reinforce(强化已有)/update(更新已有)/contradict(与已有冲突)/reject(玩家否定某项) 之一

## 输出格式
Output in JSON format. 严格输出 JSON 对象，候选记忆放在 candidates 数组里：
{"candidates": [{"category":"weapon","memory_key":"weapon.recoil_preference","memory_value":{"preference":"low","description":"倾向低后坐力枪械"},"confidence":0.85,"evidence":"玩家说'我喜欢后坐力小的枪'","source_message_ids":[3],"expression_type":"explicit","memory_action":"create"}]}

无候选记忆时输出：
{"candidates": []}

如果这批对话没有可提取的长期偏好，直接输出 {"candidates": []}，不要编造。

## 对话内容
{dialog}

## 消息id对照
{message_ids}
"""


def extract_candidates(user_id: int, dialog: list[dict]) -> list[dict]:
    """从一批对话提取候选记忆

    Args:
        user_id: 用户 id
        dialog: [{"message_id":1,"role":"user","content":"..."}, ...]
                 每条必须含 message_id（供 source_message_ids 追溯）
    Returns:
        候选记忆列表，每条是 dict 含 8 个字段。失败返回空列表（不丢对话，对话已在 chat_history）
    """
    if not dialog:
        return []

    # 只取 user 消息参与提取（assistant 回复是 AI 生成的，不是玩家偏好）
    user_msgs = [d for d in dialog if d["role"] == "user"]
    if not user_msgs:
        return []

    # 拼对话文本（只含 user 消息）
    dialog_text = "\n".join(
        f"[{d['message_id']}] {d['content']}" for d in user_msgs
    )
    # 消息id对照（让 LLM 知道每个 id 对应哪条）
    msg_ids = "\n".join(
        f"消息{d['message_id']}: 玩家说「{d['content'][:40]}...」"
        if len(d['content']) > 40 else
        f"消息{d['message_id']}: 玩家说「{d['content']}」"
        for d in user_msgs
    )

    try:
        # 用 replace 做模板替换，避免 str.format 把示例 JSON 的花括号当占位符
        prompt = (EXTRACT_PROMPT
                  .replace("{dialog}", dialog_text)
                  .replace("{message_ids}", msg_ids))
        resp = _extract_client.chat.completions.create(
            model=settings.LLM_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},  # DeepSeek JSON 模式
        )
        raw = resp.choices[0].message.content or ""
        print(f"[extractor] raw 返回 user_id={user_id}: {raw[:400]}")

        # 容错：DeepSeek JSON 模式可能返回 {"candidates":[...]} 或直接 [...]
        candidates = _parse_candidates(raw)
        print(f"[extractor] 提取到 {len(candidates)} 条候选记忆 user_id={user_id}")
        return candidates

    except Exception as e:
        import traceback
        print(f"[extractor] LLM 调用失败 user_id={user_id}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return []


def _parse_candidates(raw: str) -> list[dict]:
    """容错解析 LLM 返回，提取候选记忆数组

    处理三种情况：
    1. 直接是 JSON 数组 [...]
    2. 包在对象里 {"candidates":[...]} 或 {"memories":[...]}
    3. 带 markdown 代码块包裹
    """
    if not raw or not raw.strip():
        return []

    raw = raw.strip()

    # 去掉 markdown 代码块包裹
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        # 尝试1：直接解析（可能是数组或对象）
        data = json.loads(raw)
        if isinstance(data, list):
            return [c for c in data if isinstance(c, dict)]
        if isinstance(data, dict):
            # 尝试从对象里取数组字段
            for key in ("candidates", "memories", "result", "data"):
                if key in data and isinstance(data[key], list):
                    return [c for c in data[key] if isinstance(c, dict)]
            # 对象里只有一条
            if "category" in data or "memory_key" in data:
                return [data]
        return []
    except json.JSONDecodeError:
        # 尝试2：正则提取第一个 [ ... ] 数组
        m = re.search(r"\[.*\]", raw, re.S)
        if m:
            try:
                arr = json.loads(m.group(0))
                return [c for c in arr if isinstance(c, dict)]
            except json.JSONDecodeError:
                pass
        # 尝试3：正则提取第一个 { ... } 对象
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
                for key in ("candidates", "memories", "result", "data"):
                    if key in obj and isinstance(obj[key], list):
                        return [c for c in obj[key] if isinstance(c, dict)]
                if isinstance(obj, dict) and ("category" in obj or "memory_key" in obj):
                    return [obj]
            except json.JSONDecodeError:
                pass
    return []

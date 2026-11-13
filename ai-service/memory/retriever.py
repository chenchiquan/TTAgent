"""Memory Retriever：根据用户问题按需检索相关记忆

不默认全部塞 prompt，先用 LLM 分析问题该查哪些 category+key，
对照 Catalog 只查玩家有的，Token 预算截断。

符合需求第五节：
- "推荐适合我的枪" -> 查 weapon.preferred_type/recoil_preference/price_range/damage_preference
- "我喜欢什么地图" -> 查 map.preferred/disliked
- "这把枪多少钱" -> 不查记忆（游戏数据走 Java 接口）
- "我之前为什么不喜欢这把枪" -> 查相关 KV + weapon_preference_summary（3c）
"""
import json
import re

from openai import OpenAI

from config.settings import settings
from memory.catalog import get_catalog
from memory.store import get_active_kv_by_key

# ===== LLM 客户端（复用 DeepSeek）=====
_retrieve_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

# Token 预算：召回记忆总长度上限（字符数近似 token，留余量）
MAX_RECALL_CHARS = 800

# ===== 检索意图分析 Prompt =====
RETRIEVE_PROMPT = """你是记忆检索路由器。根据玩家的问题，判断需要检索哪些长期记忆。

## 玩家当前拥有的记忆目录
{catalog}

## 支持的记忆 key 命名空间
- weapon: weapon.preferred_type(枪械类型偏好) / weapon.price_range(价格偏好) / weapon.damage_preference(伤害偏好) / weapon.recoil_preference(后坐力偏好) / weapon.fire_rate_preference(射速偏好)
- map: map.preferred(喜欢的地图) / map.disliked(不喜欢的地图)
- ammo: ammo.preferred_type(弹药偏好)
- combat: combat.preferred_range(交战距离偏好) / combat.play_style(战斗风格) / combat.tactical_preference(战术偏好)

## 判断规则
1. 只返回玩家目录里确实有的 key（available_keys 里的），不要返回玩家没有的
2. 如果问题是游戏数据查询（价格/伤害/射速等客观数据），不需要检索记忆，返回空数组 []
3. 如果问题跟玩家偏好无关（比如纯闲聊），返回空数组 []
4. 推荐枪械类问题 -> 查 weapon 相关 key
5. 地图类问题 -> 查 map 相关 key
6. 战斗风格类问题 -> 查 combat 相关 key
7. 最多返回 5 个 key，按相关性排序

## 输出格式
Output in JSON format. 严格输出 JSON 对象：
{"need_recall": true, "retrieve_keys": ["weapon.preferred_type", "weapon.recoil_preference"]}

不需要检索时输出：
{"need_recall": false, "retrieve_keys": []}

## 玩家问题
{question}
"""


def retrieve_memories(user_id: int, question: str) -> str:
    """根据用户问题检索相关记忆，返回格式化文本（供注入 system prompt）

    Args:
        user_id: 用户 id
        question: 用户当前问题
    Returns:
        格式化的记忆文本，如：
          【玩家偏好记忆】
          - 枪械类型偏好: rifle
          - 后坐力偏好: low
          - 价格偏好: 低预算
        无相关记忆时返回空字符串 ""
    """
    # 1. 获取目录
    catalog = get_catalog(user_id)
    if not catalog["available_keys"]:
        return ""  # 玩家没有任何记忆

    # 2. LLM 分析该查哪些 key
    retrieve_keys = _analyze_retrieve_scope(question, catalog)
    if not retrieve_keys:
        return ""  # LLM 判断不需要检索

    print(f"[retriever] user_id={user_id} 检索 keys={retrieve_keys}")

    # 3. 精确查 KV 表（只查 Catalog 里有的 + LLM 要查的）
    memories = []
    for key in retrieve_keys:
        if key not in catalog["available_keys"]:
            continue  # 双重保险：LLM 返回了玩家没有的 key，跳过
        kv = get_active_kv_by_key(user_id, key)
        if kv:
            memories.append(kv)

    if not memories:
        return ""

    # 4. 按 confidence 降序排序 + Token 预算截断
    memories.sort(key=lambda m: float(m.confidence), reverse=True)
    return _format_memories(memories)


def _analyze_retrieve_scope(question: str, catalog: dict) -> list[str]:
    """LLM 分析问题该查哪些 key，返回 key 列表（只含玩家目录里有的）"""
    catalog_text = json.dumps(catalog, ensure_ascii=False, indent=2)

    try:
        prompt = (RETRIEVE_PROMPT
                  .replace("{catalog}", catalog_text)
                  .replace("{question}", question))
        resp = _retrieve_client.chat.completions.create(
            model=settings.LLM_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        print(f"[retriever] LLM 路由返回: {raw[:200]}")

        data = _parse_json(raw)
        if not data or not data.get("need_recall"):
            return []
        keys = data.get("retrieve_keys", [])
        return [k for k in keys if isinstance(k, str)]

    except Exception as e:
        import traceback
        print(f"[retriever] LLM 路由失败: {type(e).__name__}: {e}")
        traceback.print_exc()
        return []


def _format_memories(memories: list) -> str:
    """格式化记忆为注入文本，按 Token 预算截断"""
    lines = ["【玩家偏好记忆】"]
    total_chars = len(lines[0])

    for m in memories:
        pref = m.memory_value.get("preference", "")
        desc = m.memory_value.get("description", "")
        key_label = _key_label(m.memory_key)
        line = f"- {key_label}: {pref}"
        if desc:
            line += f"（{desc}）"

        if total_chars + len(line) > MAX_RECALL_CHARS:
            break  # 超预算截断
        lines.append(line)
        total_chars += len(line)

    if len(lines) <= 1:
        return ""  # 没有记忆通过预算
    return "\n".join(lines)


def _key_label(memory_key: str) -> str:
    """把 memory_key 转成中文标签（注入 prompt 更友好）"""
    labels = {
        "weapon.preferred_type": "枪械类型偏好",
        "weapon.price_range": "价格偏好",
        "weapon.damage_preference": "伤害偏好",
        "weapon.recoil_preference": "后坐力偏好",
        "weapon.fire_rate_preference": "射速偏好",
        "map.preferred": "喜欢的地图",
        "map.disliked": "不喜欢的地图",
        "ammo.preferred_type": "弹药偏好",
        "combat.preferred_range": "交战距离偏好",
        "combat.play_style": "战斗风格",
        "combat.tactical_preference": "战术偏好",
    }
    return labels.get(memory_key, memory_key)


def _parse_json(raw: str) -> dict | None:
    """容错解析 LLM 返回的 JSON 对象"""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    # 去 markdown 包裹
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None

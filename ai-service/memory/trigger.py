"""Memory Trigger：判断当前对话是否该触发记忆提取

不每轮都调 Extractor（重），先用轻量 LLM 判断是否包含值得提取的长期偏好。
trigger 只返回 True/False + 触发类型，比 Extractor 轻。

触发类型（对应需求第七节）：
- explicit：玩家明确表达长期偏好（如"我喜欢低后坐力"）-> 触发
- reinforce：再次表达已有偏好（如又说一次喜欢低后坐力）-> 触发
- update：明确修改偏好（如"我改用高后坐力了"）-> 优先触发
- none：游戏数据查询/纯闲聊/临时意图 -> 不触发

另外有轮次计数：每 N 轮强制批量检查一次（防漏）
"""
import json
import re

from openai import OpenAI

from config.settings import settings
from memory.short_term import redis_client

# ===== LLM 客户端（复用 DeepSeek）=====
_trigger_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

# 轮次计数：每 5 轮强制批量检查一次
BATCH_CHECK_ROUNDS = 5
ROUND_COUNTER_TTL = 7 * 24 * 3600  # 7 天（用户长期不聊也保留计数）

TRIGGER_PROMPT = """你是记忆提取触发判断器。判断玩家这条消息是否包含值得提取的长期偏好。

## 判断规则
1. 玩家明确表达长期偏好（如"我喜欢低后坐力的枪""我预算在5万以内"）-> explicit
2. 玩家再次强调已有偏好（如"再说一次，低后坐力最重要"）-> reinforce
3. 玩家明确修改原有偏好（如"我改用高后坐力了""以后不用步枪了"）-> update
4. 玩家询问游戏数据（如"SCAR多少钱""这把枪伤害多少"）-> none
5. 纯闲聊/打招呼/临时尝试（如"试试这把""帮我查下"）-> none
6. 不确定的不要判 explicit，宁可 none 也不要误触发

## 输出格式
Output in JSON format. 严格输出 JSON 对象：
{"should_trigger": true, "trigger_type": "explicit"}
或
{"should_trigger": false, "trigger_type": "none"}

## 玩家消息
{message}
"""


def should_trigger(user_id: int, session_id: str, message: str) -> dict:
    """判断当前消息是否该触发记忆提取

    Args:
        user_id: 用户 id
        session_id: 对话线程 id
        message: 玩家本次消息
    Returns:
        {"should_trigger": bool, "trigger_type": "explicit/reinforce/update/none",
         "reason": "批量轮次检查" 或 LLM 判断原因}
    """
    # 1. 轮次计数：每 N 轮强制批量检查
    counter = _incr_round_counter(user_id, session_id)
    if counter >= BATCH_CHECK_ROUNDS:
        _reset_round_counter(user_id, session_id)
        print(f"[trigger] 批量轮次检查 user_id={user_id} (第{counter}轮)")
        return {"should_trigger": True, "trigger_type": "reinforce",
                "reason": f"批量轮次检查(第{counter}轮)"}

    # 2. LLM 轻量判断
    result = _llm_judge(user_id, message)
    if result["should_trigger"]:
        print(f"[trigger] 触发 user_id={user_id} type={result['trigger_type']}")
    return result


def _llm_judge(user_id: int, message: str) -> dict:
    """LLM 判断消息是否包含可提取的长期偏好"""
    prompt = TRIGGER_PROMPT.replace("{message}", message)
    try:
        resp = _trigger_client.chat.completions.create(
            model=settings.LLM_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        print(f"[trigger] LLM 返回 user_id={user_id}: {raw[:200]}")

        data = _parse_json(raw)
        if not data:
            return {"should_trigger": False, "trigger_type": "none", "reason": "解析失败"}
        return {
            "should_trigger": bool(data.get("should_trigger", False)),
            "trigger_type": data.get("trigger_type", "none"),
            "reason": data.get("trigger_type", "none"),
        }
    except Exception as e:
        import traceback
        print(f"[trigger] LLM 判断失败 user_id={user_id}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return {"should_trigger": False, "trigger_type": "none", "reason": f"LLM失败: {e}"}


# ===== 轮次计数（Redis）=====
def _counter_key(user_id: int, session_id: str) -> str:
    return f"memory:round_counter:{user_id}:{session_id}"


def _incr_round_counter(user_id: int, session_id: str) -> int:
    """轮次计数 +1，返回当前计数"""
    key = _counter_key(user_id, session_id)
    count = redis_client.incr(key)
    redis_client.expire(key, ROUND_COUNTER_TTL)
    return count


def _reset_round_counter(user_id: int, session_id: str) -> None:
    """重置轮次计数（批量检查后清零）"""
    redis_client.delete(_counter_key(user_id, session_id))


def _parse_json(raw: str) -> dict | None:
    """容错解析 LLM 返回的 JSON"""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
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

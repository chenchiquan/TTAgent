"""Memory Summarizer：主题摘要生成

存 player_memory_summary 表，解决结构化 KV 无法表达的复杂背景：
- 玩家为什么不喜欢某种枪械
- 玩家曾经使用某种装备但后来放弃
- 玩家在某张地图上的长期战术习惯

按 topic 划分（不合并成总摘要），更新插新 version 旧的 superseded（禁止覆盖）。
由 consumer 攒够对话量后触发，不每轮都做。
"""
import json
import re

from openai import OpenAI

from config.settings import settings
from memory.store import Session, ChatHistory, PlayerMemorySummary, PlayerMemoryKv
from memory.models import STATUS_ACTIVE, STATUS_SUPERSEDED

# ===== LLM 客户端（复用 DeepSeek）=====
_summarize_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

# 触发摘要的对话量阈值（攒够 N 条 user 消息才摘要）
SUMMARIZE_THRESHOLD = 10

SUMMARIZE_PROMPT = """你是玩家记忆摘要器。根据玩家的结构化记忆和原始对话，生成主题摘要。

## 玩家的结构化记忆（KV）
{kv_memories}

## 原始对话（待摘要范围）
{dialog}

## 主题说明
- weapon_preference_summary: 玩家枪械偏好，包括为什么喜欢/不喜欢、偏好变化历程
- map_strategy_summary: 玩家在各地图的战术习惯
- combat_style_summary: 玩家战斗风格的演变
- equipment_selection_summary: 玩家选择/放弃装备的原因

## 规则
1. 只为这批对话真正涉及的 topic 生成摘要，不涉及的不要生成
2. 摘要要包含「为什么」和「变化历程」，不只是偏好值（偏好值在 KV 里已有）
3. 每个 topic 的摘要控制在 200 字以内
4. 如果这批对话没有值得摘要的复杂背景，返回空数组 []

## 输出格式
Output in JSON format. 严格输出 JSON 数组：
[{{"topic": "weapon_preference_summary", "summary": "玩家最初偏好低后坐力步枪，后来改用高后坐力高伤害枪械，原因是打法从防守转激进。预算始终偏低。"}}]
"""


def summarize_if_needed(user_id: int, session_id: str) -> dict:
    """检查是否需要摘要，攒够对话量则生成

    由 consumer 在提取记忆后调用。检查该 session 未摘要的 user 消息数，
    达到 SUMMARIZE_THRESHOLD 则触发摘要。

    Returns:
        {"summarized": bool, "topics": [...]} 或 {"summarized": False, "reason": ".."}
    """
    # 1. 找未摘要的对话范围（上次摘要覆盖的 message_id 之后）
    last_covered = _get_last_covered_msg_id(user_id, session_id)
    uncovered = _fetch_uncovered_dialog(user_id, session_id, last_covered)

    if len(uncovered) < SUMMARIZE_THRESHOLD:
        return {"summarized": False, "reason": f"未摘要消息 {len(uncovered)} 条，不足 {SUMMARIZE_THRESHOLD}"}

    print(f"[summarizer] 触发摘要 user_id={user_id} ({len(uncovered)} 条未摘要)")

    # 2. 取该用户的 KV 记忆（供摘要参考）
    kv_memories = _fetch_kv_memories(user_id)

    # 3. LLM 生成主题摘要
    summaries = _llm_summarize(user_id, kv_memories, uncovered)
    if not summaries:
        return {"summarized": False, "reason": "LLM 没生成摘要"}

    # 4. 写入 summary 表（每个 topic 插新 version，旧的 superseded）
    msg_ids = [d["message_id"] for d in uncovered]
    start_id = msg_ids[0] if msg_ids else 0
    end_id = msg_ids[-1] if msg_ids else 0

    saved = []
    for s in summaries:
        topic = s.get("topic", "")
        summary_text = s.get("summary", "")
        if not topic or not summary_text:
            continue
        sid = _save_summary(user_id, topic, summary_text, msg_ids, start_id, end_id)
        if sid:
            saved.append({"topic": topic, "id": sid})

    print(f"[summarizer] 保存 {len(saved)} 条摘要 user_id={user_id}: {[s['topic'] for s in saved]}")
    return {"summarized": True, "topics": saved}


def _get_last_covered_msg_id(user_id: int, session_id: str) -> int:
    """取该 session 上次摘要覆盖到的最大 message_id（0 表示没摘要过）"""
    with Session() as s:
        rows = s.query(PlayerMemorySummary).filter(
            PlayerMemorySummary.user_id == user_id,
        ).all()
        max_end = 0
        for r in rows:
            rng = r.covered_message_range or {}
            end = rng.get("end_msg_id", 0)
            if end > max_end:
                max_end = end
        return max_end


def _fetch_uncovered_dialog(user_id: int, session_id: str, last_covered: int) -> list[dict]:
    """取未摘要的对话（message_id > last_covered）"""
    with Session() as s:
        rows = s.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id,
            ChatHistory.id > last_covered,
            ChatHistory.role == "user",   # 只摘要 user 消息
        ).order_by(ChatHistory.id).all()
        return [{"message_id": r.id, "role": r.role, "content": r.content} for r in rows]


def _fetch_kv_memories(user_id: int) -> str:
    """取该用户当前有效的 KV 记忆，格式化给 LLM 参考"""
    with Session() as s:
        rows = s.query(PlayerMemoryKv).filter(
            PlayerMemoryKv.user_id == user_id,
            PlayerMemoryKv.status == STATUS_ACTIVE,
        ).all()
        if not rows:
            return "(暂无结构化记忆)"
        lines = []
        for r in rows:
            pref = r.memory_value.get("preference", "")
            lines.append(f"- {r.memory_key}: {pref} (conf={r.confidence})")
        return "\n".join(lines)


def _llm_summarize(user_id: int, kv_text: str, dialog: list[dict]) -> list[dict]:
    """LLM 生成主题摘要"""
    dialog_text = "\n".join(f"[{d['message_id']}] {d['content']}" for d in dialog)
    prompt = (SUMMARIZE_PROMPT
              .replace("{kv_memories}", kv_text)
              .replace("{dialog}", dialog_text))
    try:
        resp = _summarize_client.chat.completions.create(
            model=settings.LLM_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        print(f"[summarizer] LLM 返回 user_id={user_id}: {raw[:300]}")
        return _parse_summaries(raw)
    except Exception as e:
        import traceback
        print(f"[summarizer] LLM 失败 user_id={user_id}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return []


def _save_summary(user_id: int, topic: str, summary: str,
                  msg_ids: list, start_id: int, end_id: int) -> int | None:
    """保存主题摘要：旧版本 superseded，新版本 active（禁止覆盖）"""
    with Session() as s:
        # 旧版本标 superseded
        old = s.query(PlayerMemorySummary).filter(
            PlayerMemorySummary.user_id == user_id,
            PlayerMemorySummary.topic == topic,
            PlayerMemorySummary.status == STATUS_ACTIVE,
        ).order_by(PlayerMemorySummary.version.desc()).first()

        new_version = (old.version + 1) if old else 1
        if old:
            old.status = STATUS_SUPERSEDED

        # 插新版本
        summ = PlayerMemorySummary(
            user_id=user_id,
            topic=topic,
            summary=summary,
            source_message_ids=msg_ids,
            covered_message_range={"start_msg_id": start_id, "end_msg_id": end_id},
            version=new_version,
            status=STATUS_ACTIVE,
        )
        s.add(summ)
        s.commit()
        s.refresh(summ)
        return summ.id


def _parse_summaries(raw: str) -> list[dict]:
    """容错解析 LLM 返回的摘要数组"""
    if not raw or not raw.strip():
        return []
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [s for s in data if isinstance(s, dict)]
        if isinstance(data, dict):
            for key in ("summaries", "result", "data"):
                if key in data and isinstance(data[key], list):
                    return [s for s in data[key] if isinstance(s, dict)]
            if "topic" in data:
                return [data]
        return []
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", raw, re.S)
        if m:
            try:
                return [s for s in json.loads(m.group(0)) if isinstance(s, dict)]
            except json.JSONDecodeError:
                pass
    return []

"""DeepSeek 流式对话封装

用 OpenAI SDK 调 DeepSeek（OpenAI 兼容 API），流式返回逐 token。
阶段2：从 Redis 取短期记忆（最近 K 轮），回复后存回。
"""
from openai import OpenAI

from config.settings import settings
from memory.short_term import load_recent, append_turn

# DeepSeek 客户端（OpenAI 兼容）
client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


def chat_stream(message: str, user_id: int, session_id: str, system_prompt: str):
    """流式调用 DeepSeek，逐 token yield

    Args:
        message: 用户本次消息
        user_id: 用户 id（从 JWT 解析，用于 Redis 隔离）
        session_id: 对话 id（前端生成，区分对话线程）
        system_prompt: 系统提示词（含何涛风格）
    Yields:
        str: 逐 token 文本
    """
    # 1. 从 Redis 取最近 K 轮原文作为历史
    recent = load_recent(user_id, session_id)

    # 2. 拼 messages：system + 历史 + 本次 user
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(recent)
    messages.append({"role": "user", "content": message})

    # 3. 流式调用，同时累积完整回复
    full_reply = []
    stream = client.chat.completions.create(
        model=settings.LLM_MODEL_ID,
        messages=messages,
        stream=True,
    )
    try:
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_reply.append(delta)
                yield delta
    finally:
        # 4. 本轮结束存回 Redis（user + assistant 配对）
        append_turn(user_id, session_id, "user", message)
        reply = "".join(full_reply)
        if reply:
            append_turn(user_id, session_id, "assistant", reply)

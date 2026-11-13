"""DeepSeek 流式对话封装

用 OpenAI SDK 调 DeepSeek（OpenAI 兼容 API），流式返回逐 token。
阶段2：从 Redis 取短期记忆（最近 K 轮），回复后存回。
阶段3b：对话前检索相关长期记忆注入 system prompt（按需检索，不全部塞）。
阶段3c：对话后触发判断，满足条件发 Kafka 异步提取记忆。
"""
from openai import OpenAI

from config.settings import settings
from memory.short_term import load_recent, append_turn
from memory.retriever import retrieve_memories
from memory.trigger import should_trigger
from memory.kafka_producer import send_extract_task

# DeepSeek 客户端（OpenAI 兼容）
client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


def chat_stream(message: str, user_id: int, session_id: str, system_prompt: str):
    """流式调用 DeepSeek，逐 token yield

    Args:
        message: 用户本次消息
        user_id: 用户 id（从 JWT 解析，用于 Redis/记忆隔离）
        session_id: 对话 id（前端生成，区分对话线程）
        system_prompt: 系统提示词（含何涛风格）
    Yields:
        str: 逐 token 文本
    """
    # 1. 从 Redis 取最近 K 轮原文作为历史
    recent = load_recent(user_id, session_id)

    # 2. 检索相关长期记忆（按需，不全部塞；失败不阻塞对话）
    recall_text = ""
    try:
        recall_text = retrieve_memories(user_id, message)
        if recall_text:
            print(f"[chat] 召回记忆 user_id={user_id}:\n{recall_text[:200]}")
    except Exception as e:
        print(f"[chat] 检索记忆失败（不阻塞对话）user_id={user_id}: {e}")

    # 3. 拼 messages：system(+召回记忆) + 历史 + 本次 user
    final_system = system_prompt
    if recall_text:
        final_system = system_prompt + "\n\n" + recall_text
    messages = [{"role": "system", "content": final_system}]
    messages.extend(recent)
    messages.append({"role": "user", "content": message})

    # 4. 流式调用，同时累积完整回复
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
        # 5. 本轮结束存回 Redis（user + assistant 配对），拿 message_id 供追溯
        user_msg_id = append_turn(user_id, session_id, "user", message)
        reply = "".join(full_reply)
        if reply:
            append_turn(user_id, session_id, "assistant", reply)

        # 6. 触发判断：满足条件发 Kafka 异步提取记忆（不阻塞对话）
        if user_msg_id:
            try:
                trig = should_trigger(user_id, session_id, message)
                if trig["should_trigger"]:
                    send_extract_task(
                        user_id, session_id,
                        trig["trigger_type"], message, user_msg_id,
                    )
            except Exception as e:
                print(f"[chat] 触发/发送 Kafka 失败（不阻塞对话）user_id={user_id}: {e}")

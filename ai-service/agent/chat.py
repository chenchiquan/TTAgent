"""DeepSeek 流式对话封装

用 OpenAI SDK 调 DeepSeek（OpenAI 兼容 API），流式返回逐 token。
"""
from openai import OpenAI

from config.settings import settings

# DeepSeek 客户端（OpenAI 兼容）
client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


def chat_stream(message: str, history: list[dict], system_prompt: str):
    """流式调用 DeepSeek，逐 token yield

    Args:
        message: 用户本次消息
        history: 历史对话 [{"role":"user/assistant","content":"..."}]
        system_prompt: 系统提示词（含何涛风格）
    Yields:
        str: 逐 token 文本
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    stream = client.chat.completions.create(
        model=settings.LLM_MODEL_ID,
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

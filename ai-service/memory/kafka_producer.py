"""Kafka Producer：把待提取的对话消息发到 Kafka topic

chat.py 触发记忆提取时调用，produce 一条消息到 memory-extract topic，
立即返回不阻塞对话。Consumer 异步消费。

消息格式（JSON）：
{"user_id": 1, "session_id": "xxx", "trigger_type": "explicit",
 "message": "玩家本次消息原文", "message_id": 123}
"""
import json

from kafka import KafkaProducer

from config.settings import settings

# Kafka Producer 单例（懒加载，避免 import 时就连）
_producer: KafkaProducer | None = None


def _get_producer() -> KafkaProducer:
    """懒加载 Kafka Producer 单例"""
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=3,               # 发送失败重试 3 次
            acks="all",              # 等所有副本确认（可靠性）
        )
        print(f"[kafka_producer] 连接 {settings.KAFKA_HOST}:{settings.KAFKA_PORT}")
    return _producer


def send_extract_task(user_id: int, session_id: str, trigger_type: str,
                      message: str, message_id: int) -> bool:
    """发送记忆提取任务到 Kafka

    Args:
        user_id: 用户 id
        session_id: 对话线程 id
        trigger_type: 触发类型（explicit/reinforce/update）
        message: 玩家本次消息原文
        message_id: 消息 id（chat_history.id，供 Extractor 追溯）
    Returns:
        True=发送成功，False=发送失败（不阻塞对话）
    """
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "trigger_type": trigger_type,
        "message": message,
        "message_id": message_id,
    }
    try:
        p = _get_producer()
        future = p.send(settings.KAFKA_TOPIC_MEMORY_EXTRACT, key=str(user_id), value=payload)
        future.get(timeout=10)  # 等发送确认（10秒超时）
        print(f"[kafka_producer] 发送成功 user_id={user_id} type={trigger_type} msg_id={message_id}")
        return True
    except Exception as e:
        print(f"[kafka_producer] 发送失败（不阻塞对话）user_id={user_id}: {type(e).__name__}: {e}")
        return False


def close_producer():
    """关闭 Producer（应用退出时调）"""
    global _producer
    if _producer is not None:
        _producer.close()
        _producer = None

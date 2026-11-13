"""Kafka Consumer：订阅 memory-extract topic，异步消费调 Extractor -> Manager

独立进程运行：python -m memory.kafka_consumer
收到消息后：
1. 从 chat_history 取该消息前后几轮对话（供 Extractor 上下文）
2. 调 Extractor 提取候选记忆
3. 调 Manager 校验比对写库
失败不提交 offset，Kafka 会重投（补偿失败，对应需求第八节）
"""
import json

from kafka import KafkaConsumer

from config.settings import settings
from memory.store import Session, ChatHistory
from memory.extractor import extract_candidates
from memory.manager import process_candidates
from memory.summarizer import summarize_if_needed

# 消费时取上下文：该消息之前取几条（给 Extractor 足够上下文）
CONTEXT_ROUNDS_BEFORE = 4  # 取该消息之前 4 条（2 轮）


def start_consumer():
    """启动 Kafka Consumer，持续消费记忆提取任务"""
    consumer = KafkaConsumer(
        settings.KAFKA_TOPIC_MEMORY_EXTRACT,
        bootstrap_servers=f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        group_id=settings.KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="latest",     # 新 consumer 从最新消息开始
        enable_auto_commit=False,       # 手动提交 offset（处理成功才提交）
        max_poll_records=10,
    )
    print(f"[kafka_consumer] 启动，订阅 topic={settings.KAFKA_TOPIC_MEMORY_EXTRACT} "
          f"group={settings.KAFKA_CONSUMER_GROUP}")

    for record in consumer:
        try:
            payload = record.value
            print(f"\n[kafka_consumer] 收到消息: user_id={payload.get('user_id')} "
                  f"type={payload.get('trigger_type')} msg_id={payload.get('message_id')}")

            # 1. 消费处理
            _process_message(payload)

            # 2. 处理成功，手动提交 offset
            consumer.commit()
            print(f"[kafka_consumer] 处理完成，已提交 offset")

        except Exception as e:
            import traceback
            print(f"[kafka_consumer] 处理失败（不提交 offset，Kafka 会重投）: {type(e).__name__}: {e}")
            traceback.print_exc()
            # 不 commit，Kafka 下次会重投这条消息（补偿失败，对应需求第八节）


def _process_message(payload: dict):
    """处理一条提取任务：取上下文 -> Extractor -> Manager"""
    user_id = payload["user_id"]
    session_id = payload["session_id"]
    message_id = payload["message_id"]

    # 1. 从 chat_history 取上下文（该消息 + 之前几轮）
    dialog = _fetch_context_dialog(user_id, session_id, message_id)
    if not dialog:
        print(f"[kafka_consumer] 没取到对话上下文 user_id={user_id} msg_id={message_id}")
        return

    # 2. Extractor 提取候选记忆
    candidates = extract_candidates(user_id, dialog)
    if not candidates:
        print(f"[kafka_consumer] 没提取到候选记忆 user_id={user_id}")
        return

    # 3. Manager 校验比对写库
    result = process_candidates(user_id, candidates)
    print(f"[kafka_consumer] Manager 处理结果: {result}")

    # 4. 检查是否需要生成主题摘要（攒够对话量才触发）
    try:
        summ = summarize_if_needed(user_id, session_id)
        if summ.get("summarized"):
            print(f"[kafka_consumer] 主题摘要生成: {summ}")
    except Exception as e:
        print(f"[kafka_consumer] 摘要生成失败（不影响主流程）: {e}")


def _fetch_context_dialog(user_id: int, session_id: str, message_id: int) -> list[dict]:
    """从 chat_history 取上下文对话（该消息 + 之前几条）

    Extractor 需要上下文判断偏好，不只看单条消息。
    """
    with Session() as s:
        # 取该消息及之前 CONTEXT_ROUNDS_BEFORE 条（同 session）
        rows = s.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id,
            ChatHistory.id <= message_id,
        ).order_by(ChatHistory.id.desc()).limit(CONTEXT_ROUNDS_BEFORE + 1).all()

        # 反转成时间正序
        rows = list(reversed(rows))

        return [
            {"message_id": r.id, "role": r.role, "content": r.content}
            for r in rows
        ]


if __name__ == "__main__":
    start_consumer()

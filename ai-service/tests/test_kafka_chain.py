"""3c 端到端验证脚本：触发→Kafka→提取→落库

验证点：
1. should_trigger 判断三种消息（明确偏好/数据查询/闲聊）
2. send_extract_task 发到 Kafka（验证 Kafka 连通）
3. 手动调 consumer 的 _process_message 验证提取链路（不依赖 consumer 进程）
4. 查库验证 KV 记忆落库

注意：这个脚本不启动 consumer 进程，而是直接调 _process_message 验证提取逻辑。
Kafka 消息投递单独验证（步骤2），完整 produce->consume 链路靠你手动开 consumer 终端跑。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.trigger import should_trigger
from memory.kafka_producer import send_extract_task, close_producer
from memory.kafka_consumer import _process_message
from memory.store import Session, save_message, get_all_active_kv
from memory.catalog import invalidate_catalog
from sqlalchemy import text

TEST_USER_ID = 999997


def cleanup():
    with Session() as s:
        s.execute(text("DELETE FROM player_memory_kv WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.execute(text("DELETE FROM player_memory_summary WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.execute(text("DELETE FROM chat_history WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.commit()
    invalidate_catalog(TEST_USER_ID)
    print(f"[cleanup] 清理 user_id={TEST_USER_ID}\n")


def step1_trigger_judge():
    """步骤1：测 trigger 判断三种消息"""
    print("=" * 60)
    print("步骤1：should_trigger 判断三种消息")
    print("=" * 60)

    cases = [
        ("我喜欢低后坐力的步枪，这是我的长期偏好", "explicit", "应触发"),
        ("SCAR 多少钱", "none", "不应触发（数据查询）"),
        ("你好啊", "none", "不应触发（闲聊）"),
        ("我改用高后坐力高伤害的枪了，低后坐力不要了", "update", "应触发（修改偏好）"),
    ]

    for msg, expect_type, expect_desc in cases:
        result = should_trigger(TEST_USER_ID, "test_kafka", msg)
        triggered = result["should_trigger"]
        ttype = result["trigger_type"]
        status = "OK" if (triggered and expect_type != "none") or (not triggered and expect_type == "none") else "FAIL"
        print(f"  [{status}] 「{msg[:25]}...」 -> trigger={triggered} type={ttype} ({expect_desc})")
    print()


def step2_kafka_produce():
    """步骤2：发一条消息到 Kafka 验证连通"""
    print("=" * 60)
    print("步骤2：send_extract_task 发到 Kafka")
    print("=" * 60)

    mid = save_message(TEST_USER_ID, "test_kafka", "user", "我喜欢低后坐力的步枪，稳定压枪很重要")

    ok = send_extract_task(
        user_id=TEST_USER_ID,
        session_id="test_kafka",
        trigger_type="explicit",
        message="我喜欢低后坐力的步枪，稳定压枪很重要",
        message_id=mid,
    )
    print(f"  发送 {'成功' if ok else '失败'} (msg_id={mid})")
    print(f"  （消息已进 Kafka topic，如果你开了 consumer 进程它会消费）")
    print()
    return mid


def step3_manual_consume(mid):
    """步骤3：手动调 _process_message 验证提取链路（不依赖 consumer 进程）"""
    print("=" * 60)
    print("步骤3：手动调 _process_message 验证提取链路")
    print("=" * 60)

    # 先存几条上下文对话（让 extractor 有足够内容提取）
    save_message(TEST_USER_ID, "test_kafka", "assistant", "了解喵，低后坐力步枪有 SCAR、M4")
    save_message(TEST_USER_ID, "test_kafka", "user", "对，低后坐力是我最看重的")

    payload = {
        "user_id": TEST_USER_ID,
        "session_id": "test_kafka",
        "trigger_type": "explicit",
        "message": "我喜欢低后坐力的步枪，稳定压枪很重要",
        "message_id": mid,
    }
    _process_message(payload)
    print()


def step4_verify_kv():
    """步骤4：查库验证 KV 落库"""
    print("=" * 60)
    print("步骤4：查库验证 KV 记忆")
    print("=" * 60)

    kvs = get_all_active_kv(TEST_USER_ID)
    print(f"  active 记忆数: {len(kvs)}")
    for kv in kvs:
        print(f"    - id={kv.id} key={kv.memory_key} pref={kv.memory_value.get('preference')} "
              f"conf={kv.confidence} ev={kv.evidence_count}")
    if kvs:
        print("\n  -> 提取->落库链路验证成功")
    else:
        print("\n  -> 没落库（检查 extractor 日志，可能 LLM 没提取到）")
    print()


def main():
    print("\n" + "=" * 60)
    print("TTAgent 3c 触发->Kafka->提取->落库 验证")
    print(f"测试 user_id={TEST_USER_ID}")
    print("=" * 60 + "\n")

    cleanup()

    try:
        step1_trigger_judge()
        mid = step2_kafka_produce()
        step3_manual_consume(mid)
        step4_verify_kv()

        print("=" * 60)
        print("3c 验证完成")
        print("=" * 60)
        print("\n完整 produce->consume 链路验证：")
        print("  1. 开终端跑: python -m memory.kafka_consumer")
        print("  2. 再跑本脚本步骤2（发消息到Kafka）")
        print("  3. 看 consumer 终端是否收到并处理")
    finally:
        close_producer()
        print("\n（测试数据保留，user_id=999997）")


if __name__ == "__main__":
    main()

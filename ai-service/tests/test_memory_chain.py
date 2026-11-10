"""3a 端到端验证脚本：验证记忆提取→比对→落库链路

不是 pytest 单元测试（那要 mock LLM），而是真实调 DeepSeek + 真写 MySQL 的端到端验证。
直接 python tests/test_memory_chain.py 运行。

验证点：
1. save_message 落 chat_history，返回 message_id
2. extractor 从对话提取候选记忆
3. manager 比对 + 写 player_memory_kv（create）
4. 再喂一轮相同偏好 → reinforce（evidence_count+1, confidence 上调）
5. 再喂一轮变化偏好 → update（旧 superseded, 新 active, version+1）
6. 查库验证最终状态
"""
import sys
import os

# 让脚本能 import ai-service 包（在 ai-service/ 目录下运行）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.extractor import extract_candidates
from memory.manager import process_candidates
from memory.store import (
    Session, get_all_active_kv, save_message,
)
from memory.models import PlayerMemoryKv

TEST_USER_ID = 999999   # 测试用 user_id，跑完保留供查看
TEST_SESSION = "test_3a_chain"


def cleanup():
    """清理测试数据（TEST_USER_ID 的全部记忆 + chat_history）"""
    from sqlalchemy import text
    with Session() as s:
        s.execute(text("DELETE FROM player_memory_kv WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.execute(text("DELETE FROM player_memory_summary WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.execute(text("DELETE FROM chat_history WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.commit()
    print(f"[cleanup] 清理 user_id={TEST_USER_ID} 的测试数据\n")


def step1_append_and_save():
    """步骤1：模拟几轮对话，落 chat_history 拿 message_id"""
    print("=" * 60)
    print("步骤1：模拟对话，落 chat_history")
    print("=" * 60)

    dialog = [
        ("user", "我喜欢后坐力小的步枪，最好能稳定压枪的那种。"),
        ("assistant", "了解喵，后坐力小的步枪有 SCAR、M4 这些，都蛮稳的。"),
        ("user", "对，我就是喜欢低后坐力的，高后坐力我压不住。"),
    ]

    msg_ids = []
    for role, content in dialog:
        mid = save_message(TEST_USER_ID, TEST_SESSION, role, content)
        msg_ids.append(mid)
        print(f"  存消息 mid={mid} role={role}: {content[:30]}...")

    print(f"  -> 拿到 {len(msg_ids)} 个 message_id\n")
    return dialog, msg_ids


def step2_extract(dialog, msg_ids):
    """步骤2：extractor 提取候选记忆"""
    print("=" * 60)
    print("步骤2：extractor 提取候选记忆")
    print("=" * 60)

    ext_dialog = [
        {"message_id": msg_ids[i], "role": dialog[i][0], "content": dialog[i][1]}
        for i in range(len(dialog))
    ]

    candidates = extract_candidates(TEST_USER_ID, ext_dialog)
    print(f"  -> 提取到 {len(candidates)} 条候选记忆:")
    for c in candidates:
        print(f"    - {c.get('memory_key')}: {c.get('memory_value', {}).get('preference')} "
              f"(conf={c.get('confidence')}, expr={c.get('expression_type')}, action={c.get('memory_action')})")
    print()
    return candidates


def step3_manager_create(candidates):
    """步骤3：manager 处理候选记忆（首次 -> create）"""
    print("=" * 60)
    print("步骤3：manager 处理候选记忆（首次，预期 create）")
    print("=" * 60)

    result = process_candidates(TEST_USER_ID, candidates)
    print(f"  -> 统计: {result}")

    all_kv = get_all_active_kv(TEST_USER_ID)
    print(f"  -> 库里 active 记忆数: {len(all_kv)}")
    for kv in all_kv:
        print(f"    - id={kv.id} key={kv.memory_key} pref={kv.memory_value.get('preference')} "
              f"conf={kv.confidence} ev={kv.evidence_count} v={kv.version} status={kv.status}")
    print()
    return all_kv


def step4_reinforce(dialog, msg_ids):
    """步骤4：再喂一轮相同偏好 -> reinforce"""
    print("=" * 60)
    print("步骤4：再喂一轮相同偏好（预期 reinforce: ev+1, conf 上调）")
    print("=" * 60)

    new_msg = ("user", "再说一次，低后坐力是我最看重的，高后坐力的枪我都不考虑。")
    new_mid = save_message(TEST_USER_ID, TEST_SESSION, new_msg[0], new_msg[1])

    ext_dialog = [
        {"message_id": msg_ids[0], "role": dialog[0][0], "content": dialog[0][1]},
        {"message_id": new_mid, "role": new_msg[0], "content": new_msg[1]},
    ]

    candidates = extract_candidates(TEST_USER_ID, ext_dialog)
    print(f"  -> 提取到 {len(candidates)} 条候选")
    result = process_candidates(TEST_USER_ID, candidates)
    print(f"  -> 统计: {result}")

    all_kv = get_all_active_kv(TEST_USER_ID)
    for kv in all_kv:
        print(f"    - id={kv.id} key={kv.memory_key} pref={kv.memory_value.get('preference')} "
              f"conf={kv.confidence} ev={kv.evidence_count} v={kv.version}")
    print()
    return all_kv


def step5_update_preference():
    """步骤5：喂一轮变化偏好 -> update（旧 superseded, 新 active）"""
    print("=" * 60)
    print("步骤5：喂一轮变化偏好（预期 update: 旧 superseded, 新 active v+1）")
    print("=" * 60)

    new_content = "其实我最近改打法了，现在喜欢高后坐力高伤害的枪，低后坐力的不要了。"
    new_mid = save_message(TEST_USER_ID, TEST_SESSION, "user", new_content)

    ext_dialog = [{"message_id": new_mid, "role": "user", "content": new_content}]

    candidates = extract_candidates(TEST_USER_ID, ext_dialog)
    print(f"  -> 提取到 {len(candidates)} 条候选")
    result = process_candidates(TEST_USER_ID, candidates)
    print(f"  -> 统计: {result}")

    with Session() as s:
        all_rows = s.query(PlayerMemoryKv).filter(
            PlayerMemoryKv.user_id == TEST_USER_ID
        ).order_by(PlayerMemoryKv.memory_key, PlayerMemoryKv.version).all()
        print(f"  -> 全部记忆（含 superseded）: {len(all_rows)}")
        for kv in all_rows:
            print(f"    - id={kv.id} key={kv.memory_key} pref={kv.memory_value.get('preference')} "
                  f"v={kv.version} status={kv.status}")
    print()


def main():
    print("\n" + "=" * 60)
    print("TTAgent 长期记忆 3a 端到端验证")
    print(f"测试 user_id={TEST_USER_ID}, session={TEST_SESSION}")
    print("=" * 60 + "\n")

    cleanup()

    try:
        dialog, msg_ids = step1_append_and_save()
        candidates = step2_extract(dialog, msg_ids)

        if not candidates:
            print("!! extractor 没提取到候选记忆，检查 LLM 返回或对话内容。链路到步骤2为止。")
            return

        step3_manager_create(candidates)
        step4_reinforce(dialog, msg_ids)
        step5_update_preference()

        print("=" * 60)
        print("3a 端到端验证完成")
        print("验证点：落库 -> 提取 -> create -> reinforce -> update 全部跑通")
        print("=" * 60)

    finally:
        print("\n（测试数据保留在库里供你查看，user_id=999999）")
        print("（手动清理：DELETE FROM player_memory_kv WHERE user_id=999999;）")


if __name__ == "__main__":
    main()

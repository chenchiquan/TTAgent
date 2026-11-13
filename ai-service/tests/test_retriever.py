"""3b 端到端验证脚本：验证检索→注入链路

验证点：
1. 先用 manager 灌几条结构化记忆（weapon.preferred_type / recoil_preference / price_range）
2. get_catalog 生成目录（Redis 缓存）
3. retrieve_memories 按问题检索：
   a. "推荐一把适合我的枪" -> 应召回 weapon 相关记忆
   b. "这把枪多少钱" -> 应返回空（游戏数据不查记忆）
   c. "我喜欢什么地图" -> 应返回空（玩家没地图记忆，Catalog 过滤）
4. 验证 Catalog 失效：manager 再写一条后 catalog 自动重建
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.store import Session, save_message
from memory.models import PlayerMemoryKv, STATUS_ACTIVE
from memory.catalog import get_catalog, invalidate_catalog
from memory.retriever import retrieve_memories
from memory.manager import process_candidates

TEST_USER_ID = 999998  # 跟 3a 的 999999 区分


def cleanup():
    from sqlalchemy import text
    with Session() as s:
        s.execute(text("DELETE FROM player_memory_kv WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.execute(text("DELETE FROM chat_history WHERE user_id = :uid"), {"uid": TEST_USER_ID})
        s.commit()
    # 清 Redis catalog 缓存
    invalidate_catalog(TEST_USER_ID)
    print(f"[cleanup] 清理 user_id={TEST_USER_ID} 的测试数据\n")


def step1_seed_memories():
    """步骤1：直接往 KV 表灌几条记忆（不走 extractor，聚焦测检索）"""
    print("=" * 60)
    print("步骤1：灌几条结构化记忆")
    print("=" * 60)

    mid1 = save_message(TEST_USER_ID, "test", "user", "我喜欢步枪，低后坐力的那种")
    mid2 = save_message(TEST_USER_ID, "test", "user", "预算大概在低预算范围")

    kvs = [
        PlayerMemoryKv(user_id=TEST_USER_ID, category="weapon",
                       memory_key="weapon.preferred_type",
                       memory_value={"preference": "rifle", "description": "偏好步枪类型"},
                       confidence=0.80, expression_type="explicit",
                       source_message_ids=[mid1], status=STATUS_ACTIVE, version=1),
        PlayerMemoryKv(user_id=TEST_USER_ID, category="weapon",
                       memory_key="weapon.recoil_preference",
                       memory_value={"preference": "low", "description": "倾向低后坐力"},
                       confidence=0.85, expression_type="explicit",
                       source_message_ids=[mid1], status=STATUS_ACTIVE, version=1),
        PlayerMemoryKv(user_id=TEST_USER_ID, category="weapon",
                       memory_key="weapon.price_range",
                       memory_value={"preference": "低预算", "description": "可接受低价位枪械"},
                       confidence=0.70, expression_type="explicit",
                       source_message_ids=[mid2], status=STATUS_ACTIVE, version=1),
    ]
    with Session() as s:
        for kv in kvs:
            s.add(kv)
        s.commit()
    print(f"  灌入 {len(kvs)} 条记忆\n")
    return mid1


def step2_catalog():
    """步骤2：生成 Catalog 目录"""
    print("=" * 60)
    print("步骤2：get_catalog 生成目录")
    print("=" * 60)
    catalog = get_catalog(TEST_USER_ID)
    print(f"  categories: {catalog['available_categories']}")
    print(f"  keys: {catalog['available_keys']}")
    print(f"  topics: {catalog['available_topics']}")
    print()
    return catalog


def step3_retrieve():
    """步骤3：测三种问题的检索结果"""
    print("=" * 60)
    print("步骤3：retrieve_memories 测三种问题")
    print("=" * 60)

    questions = [
        ("推荐一把适合我的枪", "应召回 weapon 相关记忆"),
        ("这把枪多少钱", "应返回空（游戏数据不查记忆）"),
        ("我喜欢什么地图", "应返回空（玩家没地图记忆）"),
    ]

    for q, expect in questions:
        print(f"\n  问题: 「{q}」 ({expect})")
        result = retrieve_memories(TEST_USER_ID, q)
        if result:
            print(f"  召回结果:\n{result}")
        else:
            print(f"  召回结果: (空)")
    print()


def step4_catalog_invalidation():
    """步骤4：验证 Catalog 失效（再写一条后目录自动重建）"""
    print("=" * 60)
    print("步骤4：Catalog 失效验证")
    print("=" * 60)

    before = get_catalog(TEST_USER_ID)
    print(f"  失效前 keys: {before['available_keys']}")

    mid = save_message(TEST_USER_ID, "test", "user", "我打法比较激进，喜欢冲锋")
    candidates = [{
        "category": "combat",
        "memory_key": "combat.play_style",
        "memory_value": {"preference": "aggressive", "description": "激进打法"},
        "confidence": 0.80,
        "evidence": "玩家说喜欢冲锋",
        "source_message_ids": [mid],
        "expression_type": "explicit",
        "memory_action": "create",
    }]
    result = process_candidates(TEST_USER_ID, candidates)
    print(f"  manager 写入: {result}")

    after = get_catalog(TEST_USER_ID)
    print(f"  失效后 keys: {after['available_keys']}")
    if "combat.play_style" in after["available_keys"]:
        print("  -> Catalog 失效+重建成功（新增 combat.play_style）")
    else:
        print("  -> Catalog 没更新")
    print()


def main():
    print("\n" + "=" * 60)
    print("TTAgent 长期记忆 3b 检索链路验证")
    print(f"测试 user_id={TEST_USER_ID}")
    print("=" * 60 + "\n")

    cleanup()

    try:
        step1_seed_memories()
        step2_catalog()
        step3_retrieve()
        step4_catalog_invalidation()

        print("=" * 60)
        print("3b 检索链路验证完成")
        print("=" * 60)
    finally:
        print("\n（测试数据保留在库里供查看，user_id=999998）")


if __name__ == "__main__":
    main()

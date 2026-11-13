"""Memory Catalog：玩家记忆目录（Redis 缓存，不建表）

目录只记玩家有哪些 category + memory_key + topic，不记具体值。
作用：帮 Retriever 快速判断该查哪些记忆，避免盲查空 key。

读取：先查 Redis 缓存，没有就从 KV 表聚合 DISTINCT category+memory_key，写回 Redis（TTL 1h）
失效：Manager 每次 create/update/reinforce/reject 后调 invalidate_catalog 删缓存，下次读自动重建
"""
import json
from datetime import datetime

from memory.store import Session, PlayerMemoryKv
from memory.short_term import redis_client

CATALOG_TTL = 3600  # 1 小时


def _catalog_key(user_id: int) -> str:
    """Redis key：按用户隔离目录"""
    return f"memory:catalog:{user_id}"


def get_catalog(user_id: int) -> dict:
    """获取玩家记忆目录

    先查 Redis 缓存，没有就从 KV 表聚合（DISTINCT category, memory_key WHERE status=active），
    聚合结果写回 Redis（TTL 1h）。

    Returns:
        {"user_id":.., "available_categories":[..], "available_keys":[..],
         "available_topics":[..], "updated_at":".."}
    """
    key = _catalog_key(user_id)

    # 1. 先查 Redis 缓存
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)

    # 2. 缓存没有，从 KV 表聚合
    catalog = _aggregate_from_kv(user_id)

    # 3. 写回 Redis
    redis_client.setex(key, CATALOG_TTL, json.dumps(catalog, ensure_ascii=False))
    return catalog


def _aggregate_from_kv(user_id: int) -> dict:
    """从 KV 表聚合玩家当前有效的 category + memory_key"""
    categories = set()
    keys = []
    with Session() as s:
        rows = s.query(
            PlayerMemoryKv.category, PlayerMemoryKv.memory_key
        ).filter(
            PlayerMemoryKv.user_id == user_id,
            PlayerMemoryKv.status == 1,  # STATUS_ACTIVE
        ).distinct().all()

        for cat, mkey in rows:
            categories.add(cat)
            keys.append(mkey)

    return {
        "user_id": user_id,
        "available_categories": sorted(categories),
        "available_keys": sorted(keys),
        "available_topics": [],  # 3c 主题摘要生成后填充
        "updated_at": datetime.now().isoformat(),
    }


def invalidate_catalog(user_id: int) -> None:
    """删除玩家目录缓存（Manager 写库后调用，下次读自动重建）"""
    redis_client.delete(_catalog_key(user_id))

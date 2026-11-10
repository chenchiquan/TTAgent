"""短期记忆：用 Redis 存最近 K 轮对话原文，按 userId+sessionId 隔离。

key 设计：chat:recent:{userId}:{sessionId}
- userId 从 JWT 解析，保证用户隔离（A 看不到 B 的对话）
- sessionId 区分同一用户的不同对话线程
- List 结构存最近 K 轮，TTL 2h 闲置自动清理
"""
import json

import redis

from config.settings import settings

# Redis 客户端（decode_responses=True 让返回自动是 str 而不是 bytes）
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
)

MAX_ROUNDS = 10                # 保留最近 10 轮（=20 条消息）
EXPIRE_SECONDS = 2 * 60 * 60   # 2 小时不用就过期


def _key(user_id: int, session_id: str) -> str:
    """拼 Redis key：按 用户+对话 隔离，防止串号"""
    return f"chat:recent:{user_id}:{session_id}"


def load_recent(user_id: int, session_id: str) -> list[dict]:
    """取最近 K 轮原文，返回 [{"role":..,"content":..}, ...]"""
    raw = redis_client.lrange(_key(user_id, session_id), 0, -1)
    return [json.loads(item) for item in raw]


def append_turn(user_id: int, session_id: str, role: str, content: str):
    """追加一轮（role+content），截断保留最近 MAX_ROUNDS*2 条，刷新过期时间"""
    key = _key(user_id, session_id)
    redis_client.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
    redis_client.ltrim(key, -MAX_ROUNDS * 2, -1)   # 只留最后 N 条
    redis_client.expire(key, EXPIRE_SECONDS)


def trim_head(user_id: int, session_id: str, n: int) -> list[dict]:
    """删掉 Redis 最早的 n 条并返回它们（供压缩存 MySQL）。

    满容量时把将被挤出的最早几轮取出来压缩，再从 Redis 删除保留剩余。
    """
    key = _key(user_id, session_id)
    raw = redis_client.lrange(key, 0, n - 1)   # 取最早 n 条
    redis_client.ltrim(key, n, -1)             # 删掉这 n 条，保留剩余
    redis_client.expire(key, EXPIRE_SECONDS)
    return [json.loads(item) for item in raw]

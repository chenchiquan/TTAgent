"""长期记忆表 ORM 映射

3张表对应 DDL：
- player_memory_kv: 结构化玩家记忆(KV核心)
- player_memory_summary: 主题摘要
- chat_history: 原始对话(追溯依据)

JSON字段三层保障之第二层：SQLAlchemy JSON列类型，dict↔JSON字符串双向自动序列化
写入传dict，SQLAlchemy自动json.dumps交MySQL；读取自动json.loads返回dict
"""
from datetime import datetime
from typing import TypedDict

from sqlalchemy import (
    BigInteger, Column, DECIMAL, DateTime, Integer, String, Text, JSON,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MemoryValue(TypedDict, total=False):
    """结构化记忆的 value 结构约束（不是表，是类型定义）

    Manager 入库前校验：必须含 preference，description 可选
    """
    preference: str        # 偏好值，如 "low" / "步枪" / "50000"
    description: str       # 描述说明
    range: dict | None     # 价格范围等，如 {"min": 10000, "max": 50000}


class PlayerMemoryKv(Base):
    """玩家结构化记忆表（KV核心）"""
    __tablename__ = "player_memory_kv"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    category = Column(String(32), nullable=False)            # weapon/map/ammo/combat
    memory_key = Column(String(96), nullable=False)          # weapon.recoil_preference 等
    memory_value = Column(JSON, nullable=False)              # dict↔JSON 自动序列化
    confidence = Column(DECIMAL(3, 2), nullable=False, default=0.50)
    evidence_count = Column(Integer, nullable=False, default=1)
    expression_type = Column(String(24), nullable=False, default="explicit")
    source_message_ids = Column(JSON, nullable=False)        # [1, 5, 12] 消息id数组
    status = Column(String(16), nullable=False, default="active")  # active/superseded/rejected
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<PlayerMemoryKv id={self.id} user={self.user_id} key={self.memory_key} status={self.status}>"


class PlayerMemorySummary(Base):
    """玩家主题摘要表"""
    __tablename__ = "player_memory_summary"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    topic = Column(String(64), nullable=False)               # weapon_preference_summary 等
    summary = Column(Text, nullable=False)
    source_message_ids = Column(JSON, nullable=False)
    covered_message_range = Column(JSON, nullable=False)     # {"start_msg_id":N,"end_msg_id":M}
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<PlayerMemorySummary id={self.id} user={self.user_id} topic={self.topic} v{self.version}>"


class ChatHistory(Base):
    """原始对话历史表（追溯依据）"""
    __tablename__ = "chat_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # = message_id
    user_id = Column(BigInteger, nullable=False)
    session_id = Column(String(64), nullable=False)
    role = Column(String(16), nullable=False)                 # user/assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<ChatHistory id={self.id} user={self.user_id} role={self.role}>"

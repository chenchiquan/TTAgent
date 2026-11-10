"""长期记忆 MySQL 存储层

engine 复用 config.settings 的 MySQL 配置（localhost:3307, ttagent 库）
基础查询函数供 Manager(3a) 和 Retriever(3b) 调用

所有查询按 user_id 隔离，防止不同玩家记忆污染
"""
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from memory.models import Base, PlayerMemoryKv, PlayerMemorySummary, ChatHistory, STATUS_ACTIVE, STATUS_SUPERSEDED, STATUS_REJECTED

# ===== MySQL 连接（同步驱动，贴合现有同步 chat_stream）=====
engine = create_engine(
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4",
    pool_pre_ping=True,   # 连接前 ping，避免 MySQL 重启后用旧连接报错
    pool_recycle=3600,    # 1h 回收，避免 MySQL wait_timeout 断连
)
Session = sessionmaker(engine, expire_on_commit=False)


def init_tables():
    """按 ORM 模型建表（已存在则跳过）。开发期备用，生产用 DDL。"""
    Base.metadata.create_all(engine)


# ===== chat_history 基础操作 =====
def save_message(user_id: int, session_id: str, role: str, content: str) -> int:
    """存一条原始对话，返回 message_id（供记忆 source_message_ids 追溯）"""
    with Session() as s:
        msg = ChatHistory(user_id=user_id, session_id=session_id, role=role, content=content)
        s.add(msg)
        s.commit()
        s.refresh(msg)
        return msg.id


# ===== player_memory_kv 基础查询（给 Manager 用）=====
def get_active_kv_by_key(user_id: int, memory_key: str) -> PlayerMemoryKv | None:
    """查某用户某 key 的当前有效记忆（active），返回对象或 None

    Manager 判断 create/reinforce/update 时用：有 active 记忆才能 reinforce/update
    """
    with Session() as s:
        return s.query(PlayerMemoryKv).filter(
            PlayerMemoryKv.user_id == user_id,
            PlayerMemoryKv.memory_key == memory_key,
            PlayerMemoryKv.status == STATUS_ACTIVE,
        ).order_by(desc(PlayerMemoryKv.version)).first()


def get_active_kv_by_category(user_id: int, category: str) -> list[PlayerMemoryKv]:
    """查某用户某类别的全部当前有效记忆（Retriever 按 category 检索用）"""
    with Session() as s:
        return s.query(PlayerMemoryKv).filter(
            PlayerMemoryKv.user_id == user_id,
            PlayerMemoryKv.category == category,
            PlayerMemoryKv.status == STATUS_ACTIVE,
        ).order_by(desc(PlayerMemoryKv.confidence)).all()


def get_all_active_kv(user_id: int) -> list[PlayerMemoryKv]:
    """查某用户全部当前有效记忆（Catalog/全量预览用）"""
    with Session() as s:
        return s.query(PlayerMemoryKv).filter(
            PlayerMemoryKv.user_id == user_id,
            PlayerMemoryKv.status == STATUS_ACTIVE,
        ).order_by(desc(PlayerMemoryKv.confidence)).all()


def insert_kv(kv: PlayerMemoryKv) -> int:
    """插入一条新记忆，返回 id"""
    with Session() as s:
        s.add(kv)
        s.commit()
        s.refresh(kv)
        return kv.id


def supersede_kv(kv_id: int) -> None:
    """把某条记忆标记为 superseded（被新偏好取代）

    Manager update 时：旧记忆 superseded，新记忆 insert 成 active
    只改 status，保留数据可追溯
    """
    with Session() as s:
        s.query(PlayerMemoryKv).filter(PlayerMemoryKv.id == kv_id).update(
            {PlayerMemoryKv.status: STATUS_SUPERSEDED}
        )
        s.commit()


def reject_kv(kv_id: int) -> None:
    """把某条记忆标记为 rejected（玩家明确否定）"""
    with Session() as s:
        s.query(PlayerMemoryKv).filter(PlayerMemoryKv.id == kv_id).update(
            {PlayerMemoryKv.status: STATUS_REJECTED}
        )
        s.commit()


def reinforce_kv(kv_id: int, new_confidence: float, new_source_ids: list) -> None:
    """强化已有记忆：evidence_count+1，更新 confidence，追加 source_message_ids

    Manager reinforce 时用。source_message_ids 追加新消息id（不覆盖旧的）
    """
    with Session() as s:
        kv = s.query(PlayerMemoryKv).filter(PlayerMemoryKv.id == kv_id).first()
        if kv:
            kv.evidence_count = kv.evidence_count + 1
            kv.confidence = new_confidence
            # 追加新的来源 id（去重）
            existing = set(kv.source_message_ids or [])
            existing.update(new_source_ids)
            kv.source_message_ids = list(existing)
            s.commit()

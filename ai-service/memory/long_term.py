"""长期记忆：把多轮对话压缩成摘要存 MySQL，按 userId 隔离。

设计参考 hello_agent.pdf 第8章记忆系统：
- 工作记忆(Redis 短期) → 情景记忆(MySQL 压缩摘要) 的整合(Consolidation)
- 压缩时调 LLM 提取摘要 + 标签 + 重要性，存 memory 表
- recall_count / is_active / is_permanent 留给阶段4召回升级 + 阶段5定时维护

跨对话召回说明：
- session_id 只记录"这条摘要来自哪个对话"，召回时按 user_id 检索不卡 session_id
"""
import json
from datetime import datetime

from openai import OpenAI
from sqlalchemy import (
    BigInteger, Column, DECIMAL, DateTime, Integer, SmallInteger, String, Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings

# ===== MySQL 连接（同步驱动，贴合现有同步 chat_stream）=====
engine = create_engine(
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4",
    pool_pre_ping=True,   # 连接前 ping，避免 MySQL 重启后用旧连接报错
    pool_recycle=3600,    # 1h 回收，避免 MySQL wait_timeout 断连
)
Session = sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


class Memory(Base):
    """长期记忆表 ORM 映射"""
    __tablename__ = "memory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    session_id = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(255))
    importance = Column(DECIMAL(3, 2), nullable=False, default=0.50)
    recall_count = Column(Integer, nullable=False, default=0)
    is_active = Column(SmallInteger, nullable=False, default=1)
    is_permanent = Column(SmallInteger, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== 压缩用的 LLM 客户端（复用 DeepSeek）=====
_compress_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
)

COMPRESS_PROMPT = """你是对话记忆压缩器。把下面多轮对话压缩成一条长期记忆摘要，供后续召回使用。
要求：
1. 提取关键事实、用户偏好、讨论结论，丢弃寒暄和废话
2. 摘要控制在 100 字以内，第三人称客观陈述
3. 给 3-5 个标签（逗号分隔，便于检索，如：枪械,SCAR,改枪推荐,价格）
4. 评估重要性 0.0-1.0（涉及用户核心偏好/关键结论 >0.7，普通闲聊 <0.4）
输出严格 JSON：{"summary":"...","tags":"...","importance":0.0}

对话内容：
{dialog}"""


def compress_and_store(user_id: int, session_id: str, turns: list[dict]) -> dict | None:
    """把几轮对话压缩成一条摘要存 MySQL。

    Args:
        user_id: 用户 id
        session_id: 对话线程 id（记录来源，召回时不卡）
        turns: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    Returns:
        {"id": .., "summary": .., "tags": .., "importance": ..} 或 None(失败)
    """
    dialog = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
    try:
        resp = _compress_client.chat.completions.create(
            model=settings.LLM_MODEL_ID,
            messages=[{"role": "user", "content": COMPRESS_PROMPT.format(dialog=dialog)}],
            response_format={"type": "json_object"},  # DeepSeek 支持 JSON 模式
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[long_term] 压缩失败 user_id={user_id}: {e}")
        return None

    summary = (data.get("summary") or "").strip()
    if not summary:
        print(f"[long_term] 压缩结果为空 user_id={user_id}: {data}")
        return None

    tags = (data.get("tags") or "").strip()
    importance = max(0.0, min(1.0, float(data.get("importance", 0.5))))

    try:
        with Session() as s:
            mem = Memory(
                user_id=user_id,
                session_id=session_id,
                content=summary,
                tags=tags,
                importance=importance,
            )
            s.add(mem)
            s.commit()
            s.refresh(mem)
            return {"id": mem.id, "summary": summary, "tags": tags, "importance": importance}
    except Exception as e:
        print(f"[long_term] 写 MySQL 失败 user_id={user_id}: {e}")
        return None

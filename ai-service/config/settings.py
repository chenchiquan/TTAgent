"""TTAgent 配置读取

从 .env 读取配置，不写死任何 Key。
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    # LLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_MODEL_ID: str = os.getenv("LLM_MODEL_ID", "")

    # Embedding
    EMBED_API_KEY: str = os.getenv("EMBED_API_KEY", "")
    EMBED_MODEL_NAME: str = os.getenv("EMBED_MODEL_NAME", "text-embedding-v3")

    # MySQL（后续使用）
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "ttagent")

    # Redis（短期记忆）
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # JWT（后续使用）
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


settings = Settings()

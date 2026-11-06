"""Chroma 记忆系统骨架

TODO: 等用户提供几百条何涛聊天样本后，实现：
1. store_hetao_samples() —— 向量化存入何涛话语（动态 Few-shot 检索库）
2. retrieve_hetao_examples() —— 检索与当前话题最相关的何涛原话，注入 prompt 做 Few-shot
3. 对话历史记忆 —— 存用户与助手对话，长期保持上下文

Embedding 用 DashScope（settings.EMBED_API_KEY）。
"""
import chromadb

from config.settings import settings

# Chroma 本地持久化客户端，数据存 ai-service/chroma_data/
_client = chromadb.PersistentClient(path="./chroma_data")


def get_collection(name: str):
    """获取或创建集合"""
    return _client.get_or_create_collection(name=name)


def store_hetao_samples(samples: list[dict]):
    """存何涛话语样本（待实现）

    Args:
        samples: [{"id": "h1", "content": "何涛说过的话", "metadata": {"time": "..."}}]
    TODO: 用 DashScope Embedding 向量化后存入 Chroma
    """
    # TODO: 待几百条样本到位后实现
    pass


def retrieve_hetao_examples(query: str, top_k: int = 3) -> list[str]:
    """检索与 query 最相关的何涛话语（动态 Few-shot）

    Args:
        query: 用户当前消息
        top_k: 返回几条
    Returns:
        最相关的何涛原话列表
    TODO: 待样本入库后实现检索
    """
    # TODO: 待几百条样本到位后实现
    return []

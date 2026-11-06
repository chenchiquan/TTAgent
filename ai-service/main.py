"""TTAgent AI 服务

提供 Agent 对话接口（DeepSeek 流式 + SSE），供 Java 后端 WebClient 转发给前端。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.chat import chat_stream
from prompt.system_prompt import SYSTEM_PROMPT

app = FastAPI(title="TTAgent AI Service", version="0.0.1")

# 允许 Java 后端跨域调用（Java 在 8080，Python 在 8000）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]


@app.get("/")
def root():
    return {"name": "TTAgent AI Service", "status": "running", "version": "0.0.1"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    """流式对话接口：SSE 返回逐 token，Java 转发给前端"""
    def event_stream():
        try:
            for chunk in chat_stream(req.message, req.history, SYSTEM_PROMPT):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

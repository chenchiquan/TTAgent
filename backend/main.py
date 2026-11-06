"""TTAgent 后端入口

最小可运行骨架，后续逐步补充 Agent、工具、鉴权等模块。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TTAgent",
    description="三角洲行动游戏助手后端",
    version="0.0.1",
)

# 允许前端跨域访问，开发阶段先放开所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "TTAgent",
        "status": "running",
        "version": "0.0.1",
    }


@app.get("/health")
def health():
    return {"status": "ok"}

# TTAgent TODO 日志

## 2026-11-04

### 已完成

- 创建项目目录结构
- 创建 FastAPI 最小骨架 `backend/main.py`
- 创建配置读取 `backend/config/settings.py`
- 创建 `.env.example`
- 创建 `requirements.txt`
- 创建路线图 `docs/roadmap.md`
- 创建 TODO 日志 `docs/todo.md`
- 创建 Vue 占位页面 `frontend/index.html`
- 创建前端说明 `frontend/README.md`
- 升级前端为 Vite + Vue 正式工程
- 后端添加 CORS 跨域支持

### 待办

- [ ] 安装依赖并测试 FastAPI 启动
- [ ] 接入 Agent（HelloAgents + DeepSeek）
- [ ] 接入记忆系统（Chroma + DashScope）
- [ ] 实现枪械数据工具
- [ ] 实现价格查询工具
- [ ] 实现改枪推荐工具
- [ ] 实现 APScheduler 定时价格同步
- [ ] 设计 MySQL 表结构（等用户提供完整信息）
- [ ] 实现 JWT 鉴权
- [ ] 搭建 Vue 前端
- [ ] Docker 容器化（backend / frontend / mysql）
- [ ] 编写 docker-compose.yml

### 说明

- MySQL 表结构暂不创建，等用户补充完整业务信息后再设计。
- 从零开始，不依赖 helloAgent 学习项目代码。
- 先单用户跑通，后期扩展多用户。

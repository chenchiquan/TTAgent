# TTAgent 路线图

## 项目目标

做一个三角洲行动游戏助手，功能包括：

1. 枪械数值分析（击杀数据、损耗分析等）
2. 定时获取最新价格信息
3. 根据输入语句推荐改枪
4. 定时同步最新物价
5. 登录校验、历史对话、鉴权
6. 后期 Web 界面（Vue）
7. 记忆系统，根据用户偏好推荐枪械

## 技术栈

- Python + FastAPI（后端）
- Vue 3 + Vite（前端，前后端分离）
- HelloAgents + DeepSeek（Agent）
- Chroma + DashScope Embedding（记忆）
- APScheduler（定时任务）
- MySQL（后续，数据持久化）
- Spring Boot（仅必要时辅助）
- Docker / Docker Compose（后期容器化部署）

## 阶段规划

### 阶段 1：基础框架（已完成）

- [x] 目录结构
- [x] FastAPI 骨架 + CORS
- [x] 配置读取
- [x] 依赖清单
- [x] 前后端分离（Vite + Vue）
- [x] TODO 日志

### 阶段 2：核心功能

- [ ] Agent 接入
- [ ] 枪械数据工具
- [ ] 价格查询工具
- [ ] 改枪推荐工具
- [ ] 记忆系统接入

### 阶段 3：数据与定时任务

- [ ] MySQL 表结构设计
- [ ] 价格定时同步
- [ ] 数据维护流程

### 阶段 4：鉴权与多用户

- [ ] JWT 鉴权
- [ ] 用户表
- [ ] 历史对话持久化

### 阶段 5：前端功能

- [ ] Vue 前端对接后端接口
- [ ] 对话界面
- [ ] 枪械分析界面
- [ ] 改枪推荐界面
- [ ] 价格展示界面

### 阶段 6：Docker 容器化

- [ ] 编写 backend Dockerfile
- [ ] 编写 frontend Dockerfile（Nginx 托管）
- [ ] 编写 docker-compose.yml
- [ ] MySQL 容器化
- [ ] 统一网络与服务名
- [ ] 环境变量通过 .env 注入

Docker 部署目标：

```text
docker-compose up
├── frontend   (Nginx, 80)
├── backend    (FastAPI, 8000)
├── mysql      (3306)
└── java       (可选, 8080)
```

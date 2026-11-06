# TTAgent 前端

## 技术栈

- Vue 3
- Vite 5
- axios

## 目录结构

```text
frontend/
├── src/
│   ├── api/
│   │   └── index.js      # axios 实例
│   ├── App.vue           # 根组件
│   └── main.js           # 入口
├── index.html
├── vite.config.js
├── package.json
└── .env.example
```

## 环境变量

复制 `.env.example` 为 `.env`：

```dotenv
VITE_API_BASE=http://localhost:8000
```

## 运行

```powershell
cd frontend
npm install
npm run dev
```

默认端口：`http://localhost:5173`

## 构建

```powershell
npm run build
```

构建产物在 `dist/`，可由 Nginx 或后端托管。

## 前后端通信

```text
Vue (5173) --HTTP--> FastAPI (8000)
```

后端已配置 CORS，允许跨域。

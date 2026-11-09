# ===== 构建阶段：node 编译静态文件 =====
FROM node:20-alpine AS builder
WORKDIR /build
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build   # 产物在 dist/

# ===== 运行阶段：nginx 托管静态文件 =====
FROM nginx:stable-alpine
# 把构建产物拷到 nginx 默认目录
COPY --from=builder /build/dist /usr/share/nginx/html
# 自定义 nginx 配置（静态托管 + 反代 /api 到 Java）
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

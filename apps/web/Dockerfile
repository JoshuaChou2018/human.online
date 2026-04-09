FROM node:20-alpine

WORKDIR /app

# 设置构建参数
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# 安装依赖
COPY package.json ./
RUN npm install

# 复制应用代码
COPY . .

# 构建生产版本（如果需要）
# RUN npm run build

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "run", "dev"]

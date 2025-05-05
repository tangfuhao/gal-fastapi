# Gala API

基于 FastAPI 的后端服务，用于小说到 Galgame 的转换。

## 技术栈

- FastAPI
- MongoDB
- DeepSeek API
- Google OAuth
- Railway 部署

## 本地开发

1. 克隆仓库：
```bash
git clone <repository-url>
cd gala
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

5. 运行开发服务器：
```bash
uvicorn main:app --reload
```

## Railway 部署

1. 在 Railway.app 创建新项目

2. 连接 GitHub 仓库

3. 配置环境变量：
   - 在 Railway 控制台添加所有必要的环境变量
   - 参考 `.env.example` 文件

4. 部署：
   - Railway 会自动检测配置并部署
   - 使用 `railway.json` 中的配置
   - 自动运行健康检查

## 环境变量

必要的环境变量：

- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `MONGODB_URL`: MongoDB 连接 URL
- `GOOGLE_CLIENT_ID`: Google OAuth 客户端 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 客户端密钥
- `FRONTEND_URL`: 前端应用 URL
- `SECRET_KEY`: 会话密钥

## API 文档

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- 健康检查: `/api/health`

## 监控和日志

Railway 提供内置的监控和日志功能：

- 应用性能监控
- 资源使用统计
- 详细的日志记录
- 健康检查状态

## 故障排除

1. 如果健康检查失败：
   - 检查 MongoDB 连接
   - 验证环境变量配置
   - 查看应用日志

2. 如果部署失败：
   - 确保 `requirements.txt` 是最新的
   - 检查 `railway.json` 配置
   - 验证 Python 版本兼容性

pipreqs . --force 
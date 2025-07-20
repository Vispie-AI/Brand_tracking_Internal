# 部署说明 - 从 Localhost 到在线版本

本项目是一个品牌分析器应用，包含 React 前端和 Flask 后端。

## 项目结构
- **前端**: React 应用 (src/ 目录)
- **后端**: Flask Python API (app.py)

## 在线部署步骤

### 1. 后端部署到 Railway

1. 访问 [Railway.app](https://railway.app)
2. 使用 GitHub 账号登录
3. 创建新项目，选择 "Deploy from GitHub repo"
4. 选择这个仓库
5. Railway 会自动检测到 Python 项目并部署
6. 部署完成后，获取后端域名（例如：`https://your-app.railway.app`）

**环境变量设置**（在 Railway 项目设置中）：
```
PORT=5000
DEBUG=False
```

### 2. 前端部署到 Vercel

1. 访问 [Vercel.com](https://vercel.com)
2. 使用 GitHub 账号登录
3. 点击 "New Project"，选择这个仓库
4. 在环境变量设置中添加：
```
REACT_APP_API_BASE_URL=https://your-app.railway.app
```
5. 点击 "Deploy" 开始部署

### 3. 本地开发环境设置

创建 `.env.local` 文件：
```
REACT_APP_API_BASE_URL=http://localhost:5000
```

运行本地开发：
```bash
# 后端 (终端1)
python app.py

# 前端 (终端2)
npm start
```

## 配置说明

### 前端配置
- 使用环境变量 `REACT_APP_API_BASE_URL` 来配置 API 地址
- 开发环境：`http://localhost:5000`
- 生产环境：您的 Railway 部署域名

### 后端配置
- Flask 应用监听环境变量 `PORT`（默认 5000）
- 通过 `DEBUG` 环境变量控制调试模式
- CORS 配置允许跨域请求

## 部署后验证

1. 访问 Vercel 提供的前端域名
2. 尝试上传文件并运行分析
3. 检查 Railway 后端日志确认 API 请求正常

## 文件结构
```
├── src/                    # React 前端代码
├── app.py                  # Flask 后端主文件
├── universal_brand_analyzer.py  # 品牌分析核心逻辑
├── requirements.txt        # Python 依赖
├── package.json           # Node.js 依赖
├── vercel.json            # Vercel 部署配置
├── railway.json           # Railway 部署配置
└── Procfile              # Heroku 部署配置（备选）
```

## 注意事项

1. **文件上传限制**: 当前配置为最大 50MB
2. **数据存储**: 上传的文件和分析结果存储在临时目录
3. **任务清理**: 系统会自动清理超过 24 小时的旧任务
4. **并发处理**: 后端使用线程池处理多个分析任务

如有问题，请检查：
- Railway 后端部署状态和日志
- Vercel 前端部署状态
- 环境变量是否正确设置
- CORS 配置是否允许前端域名访问 
# 品牌创作者分析器

AI驱动的创作者品牌关联性分析工具，能够精准识别官方品牌账号、矩阵账号和UGC创作者。

## 项目架构

本项目采用前后端分离架构：

- **前端**: Next.js + React + TypeScript + Tailwind CSS
- **后端**: Flask + Python API
- **部署**: 前端部署到Vercel，后端部署到任意支持Python的云平台

## 功能特性

- 🎯 **精准分类**: 将创作者分为官方品牌账号、矩阵账号、UGC创作者三大类
- 🤖 **AI驱动**: 使用Google Gemini AI进行智能分析
- 📊 **实时进度**: 实时显示分析进度和日志
- 📈 **数据可视化**: 清晰的统计图表和数据展示
- 📁 **批量处理**: 支持大规模JSON数据文件上传
- 💾 **结果导出**: 分别导出品牌相关和非品牌相关的CSV文件

## 本地开发

### 前端开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 打开浏览器访问 http://localhost:3000
```

### 后端开发

```bash
# 安装Python依赖
pip install -r requirements.txt

# 设置环境变量
export GOOGLE_API_KEY="your_google_api_key"

# 启动Flask API服务器
python app.py

# API将在 http://localhost:5000 运行
```

## 部署指南

### 前端部署到Vercel

1. **连接Git仓库**:
   ```bash
   # 推送代码到Git仓库
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Vercel部署**:
   - 访问 [Vercel Dashboard](https://vercel.com/dashboard)
   - 点击 "New Project"
   - 导入你的Git仓库
   - Vercel会自动检测到Next.js项目并配置构建设置

3. **环境变量配置**:
   在Vercel项目设置中添加：
   ```
   API_BASE_URL=https://your-backend-domain.com
   ```

### 后端部署选项

#### 选项1: Railway
```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录Railway
railway login

# 初始化项目
railway init

# 部署
railway up
```

#### 选项2: Heroku
```bash
# 创建Procfile
echo "web: python app.py" > Procfile

# 初始化Git并部署
git init
heroku create your-app-name
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### 选项3: 阿里云/腾讯云
上传代码到云服务器，使用Gunicorn运行Flask应用：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 配置连接

部署完成后，需要更新前端的API连接：

1. 在Vercel环境变量中设置 `API_BASE_URL` 为你的后端域名
2. 确保后端API支持CORS（已配置）
3. 测试前后端连接是否正常

## API接口文档

### 文件上传
```
POST /api/upload
Content-Type: multipart/form-data

Response: {
  "task_id": "uuid"
}
```

### 查询分析状态
```
GET /api/status/{task_id}

Response: {
  "status": "pending|running|completed|error",
  "progress": "描述文本",
  "results": { ... },
  "logs": [ ... ]
}
```

### 下载结果文件
```
GET /api/download/{task_id}/{file_type}
file_type: "brand" | "non_brand"

Response: CSV文件下载
```

### 健康检查
```
GET /api/health

Response: {
  "status": "healthy",
  "message": "Brand Analyzer API is running"
}
```

## 项目结构

```
Brand_tracking_Internal/brand_tool_demo/
├── app.py                    # Flask API后端
├── universal_brand_analyzer.py # 核心分析逻辑
├── requirements.txt          # Python依赖
├── package.json             # Node.js依赖
├── next.config.js           # Next.js配置
├── tailwind.config.js       # Tailwind CSS配置
├── tsconfig.json           # TypeScript配置
├── vercel.json             # Vercel部署配置
├── pages/
│   ├── _app.tsx            # Next.js App组件
│   └── index.tsx           # 主页面
├── styles/
│   └── globals.css         # 全局样式
├── uploads/                # 上传文件存储
└── analyzed_data/          # 分析结果存储
```

## 环境变量

### 后端环境变量
```bash
GOOGLE_API_KEY=your_google_gemini_api_key
PORT=5000
```

### 前端环境变量
```bash
API_BASE_URL=http://localhost:5000  # 开发环境
API_BASE_URL=https://your-api-domain.com  # 生产环境
```

## 数据格式

### 输入JSON格式
支持以下两种格式：

1. **嵌套格式**:
```json
{
  "creators": [
    {
      "username": "example_user",
      "bio": "个人简介",
      "profile": {
        "description": "详细描述"
      }
    }
  ]
}
```

2. **扁平格式**:
```json
[
  {
    "username": "example_user",
    "bio": "个人简介",
    "description": "详细描述"
  }
]
```

### 输出CSV格式
```csv
username,bio,is_brand,is_matrix_account,is_ugc_creator,brand_name
example_user,个人简介,True,False,False,BrandName
```

## 分类逻辑

- **官方品牌账号**: 用户名包含品牌名且简介推广同一产品
- **矩阵账号**: 与品牌有明确关联但非官方账号
- **UGC创作者**: 有明确合作标识（#ad, #sponsored等）的创作者

## 技术栈

- **前端**: Next.js 14, React 18, TypeScript, Tailwind CSS, Axios, Lucide React
- **后端**: Flask, Google Generative AI, Python 3.8+
- **部署**: Vercel (前端), Railway/Heroku/云服务器 (后端)

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查环境变量 `API_BASE_URL` 是否正确
   - 确认后端服务是否正常运行
   - 检查CORS配置

2. **文件上传失败**
   - 确认文件格式为JSON
   - 检查文件大小是否超过50MB限制
   - 验证JSON格式是否正确

3. **分析失败**
   - 检查Google API密钥是否有效
   - 确认网络连接正常
   - 查看后端日志获取详细错误信息

### 联系支持

如有问题，请检查：
1. 后端日志输出
2. 浏览器开发者工具控制台
3. 网络连接状态
4. API密钥配置

## 许可证

MIT License 
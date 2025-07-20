#!/bin/bash

echo "🚀 品牌分析器 - 在线部署配置脚本"
echo "=================================="

# 检查必要的文件
echo "✅ 检查项目文件..."
if [ ! -f "package.json" ]; then
    echo "❌ package.json 未找到"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "❌ app.py 未找到"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 未找到"
    exit 1
fi

echo "✅ 所有必要文件都存在"

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install

echo "🔧 创建环境变量文件..."
cat > .env.local << EOL
# 本地开发环境配置
REACT_APP_API_BASE_URL=http://localhost:5000
EOL

echo "✅ 环境变量文件创建完成"

echo ""
echo "🎯 下一步部署说明："
echo "==================="
echo "1. 推送代码到 GitHub 仓库"
echo "2. 部署后端到 Railway:"
echo "   - 访问 https://railway.app"
echo "   - 创建新项目，连接 GitHub 仓库"
echo "   - 添加环境变量: PORT=5000, DEBUG=False"
echo ""
echo "3. 部署前端到 Vercel:"
echo "   - 访问 https://vercel.com"
echo "   - 创建新项目，连接 GitHub 仓库"
echo "   - 添加环境变量: REACT_APP_API_BASE_URL=https://你的railway域名.railway.app"
echo ""
echo "4. 本地开发运行:"
echo "   后端: python app.py"
echo "   前端: npm start"
echo ""
echo "详细说明请查看 DEPLOYMENT.md 文件" 
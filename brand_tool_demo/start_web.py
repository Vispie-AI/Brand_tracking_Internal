#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌分析器 Web应用启动脚本
"""

import os
import sys

def main():
    print("正在启动品牌创作者分析器 Web应用...")
    print("=" * 50)
    
    # 检查依赖
    try:
        import flask
        print("✓ Flask 已安装")
    except ImportError:
        print("✗ Flask 未安装，请运行: pip install flask")
        return
    
    try:
        from google import genai
        print("✓ Google GenAI 已安装")
    except ImportError:
        print("✗ Google GenAI 未安装，请运行: pip install google-genai")
        return
    
    try:
        import requests
        print("✓ Requests 已安装")
    except ImportError:
        print("✗ Requests 未安装，请运行: pip install requests")
        return
    
    print("✓ 所有依赖都已安装")
    print("=" * 50)
    
    # 检查必要文件
    if not os.path.exists('universal_brand_analyzer.py'):
        print("✗ 找不到 universal_brand_analyzer.py 文件")
        return
    
    if not os.path.exists('app.py'):
        print("✗ 找不到 app.py 文件")
        return
    
    if not os.path.exists('templates/index.html'):
        print("✗ 找不到 templates/index.html 文件")
        return
    
    print("✓ 所有必要文件都存在")
    print("=" * 50)
    
    # 创建必要的目录
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('analyzed_data', exist_ok=True)
    print("✓ 创建了必要的目录")
    
    print("\n🚀 启动Web应用...")
    print("📱 访问地址: http://localhost:5000")
    print("🔄 按 Ctrl+C 停止应用")
    print("=" * 50)
    
    # 启动Flask应用
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main() 
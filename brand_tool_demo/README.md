# 品牌创作者分析器 Web应用

这是一个用于分析TikTok创作者品牌关联性的Web应用，能够将创作者分类为官方品牌账号、矩阵账号和UGC创作者。

## 功能特性

- 🔍 **智能分析**: 使用AI分析TikTok创作者的品牌关联性
- 📊 **详细分类**: 将创作者分为官方品牌、矩阵账号、UGC创作者三类
- 📈 **实时监控**: 实时显示分析进度和详细日志
- 📋 **统计报告**: 提供完整的分析统计和比例分布
- 💾 **文件导出**: 生成品牌相关和非品牌两个CSV文件
- 🌐 **Web界面**: 美观易用的Web界面

## 环境要求

- Python 3.7+
- Flask 2.3.3+
- Google GenAI API
- 稳定的网络连接

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：
```bash
pip install Flask==2.3.3
pip install google-genai==0.5.0
pip install requests==2.31.0
pip install Werkzeug==2.3.7
```

### 2. 配置API密钥

确保在 `universal_brand_analyzer.py` 中配置了有效的API密钥：
- `GEMINI_API_KEY`: Google Gemini API密钥
- `RAPIDAPI_KEY`: RapidAPI密钥（用于TikTok数据获取）

### 3. 启动应用

方法一：使用启动脚本（推荐）
```bash
python start_web.py
```

方法二：直接启动Flask应用
```bash
python app.py
```

### 4. 访问应用

打开浏览器访问：`http://localhost:5000`

## 使用方法

### 1. 上传文件
- 支持拖拽上传或点击选择JSON文件
- 文件大小限制：50MB
- 支持的数据格式：
  - 嵌套格式（如creator_list.json）
  - 扁平格式（如shoe_list.json）

### 2. 监控进度
- 实时显示分析进度
- 查看详细的分析日志
- 观察处理统计信息

### 3. 查看结果
分析完成后将显示：
- 总创作者数量
- 品牌相关账号数量
- 官方品牌账号、矩阵账号、UGC创作者的数量和比例
- brand_related_list中的详细分布

### 4. 下载结果
- **品牌相关账号CSV**: 包含所有品牌相关的创作者
- **非品牌账号CSV**: 包含普通创作者和其他非品牌相关账号

## 数据格式

### 输入JSON格式
支持两种格式：

**嵌套格式**:
```json
[
  {
    "video_id": "123456789",
    "basic_info": {
      "author_unique_id": "creator_name",
      "author_nickname": "Creator Display Name",
      "create_time": "1641024000"
    },
    "title": "Video title",
    "description": "Video description"
  }
]
```

**扁平格式**:
```json
[
  {
    "video_id": "123456789",
    "author_unique_id": "creator_name",
    "author_nickname": "Creator Display Name",
    "create_time": "1641024000",
    "title": "Video title",
    "signature": "Creator bio"
  }
]
```

### 输出CSV格式
生成的CSV文件包含以下字段：
- `video_id`: 视频ID
- `author_unique_id`: 创作者唯一ID
- `author_link`: 创作者TikTok链接
- `signature`: 创作者简介
- `is_brand`: 是否为官方品牌账号
- `is_matrix_account`: 是否为矩阵账号
- `is_ugc_creator`: 是否为UGC创作者
- `brand_name`: 关联品牌名称
- `analysis_details`: 分析详情
- `author_followers_count`: 粉丝数
- `author_followings_count`: 关注数
- `videoCount`: 视频数量
- `author_avatar`: 头像链接
- `create_times`: 创建时间

## 分类标准

### 官方品牌账号 (OFFICIAL_BRAND)
- 用户名包含品牌/产品名称
- 简介直接推广自己的产品/服务
- 明确的公司品牌和产品所有权
- 例如：@getnoteai, @ainotebook_app

### 矩阵账号 (MATRIX_ACCOUNT)
- 个人资料与特定品牌有明显联系
- 简介提及为特定公司/品牌工作
- 与特定品牌有明确的隶属关系或雇佣关系
- 例如：员工账号、品牌大使

### UGC创作者 (UGC_CREATOR)
- 有明确品牌合作信号的创作者
- 包含#ad、#sponsored、#partner标签
- 有折扣码或联盟链接
- 与品牌有商业合作但非雇佣关系

## 技术架构

### 后端
- **Flask**: Web框架
- **Threading**: 多线程处理分析任务
- **Google GenAI**: AI分析引擎
- **RapidAPI**: TikTok数据获取

### 前端
- **Bootstrap 5**: UI框架
- **JavaScript**: 异步交互
- **WebSocket-like**: 实时状态更新

### 文件结构
```
brand_tool_demo/
├── app.py                          # Flask应用主文件
├── universal_brand_analyzer.py     # 分析器核心逻辑
├── start_web.py                    # 启动脚本
├── requirements.txt                # 依赖列表
├── README.md                       # 说明文档
├── templates/
│   └── index.html                  # 前端页面
├── uploads/                        # 上传文件目录
└── analyzed_data/                  # 分析结果目录
```

## 注意事项

1. **API限制**: 受Gemini API和RapidAPI的调用限制
2. **处理时间**: 大文件分析可能需要较长时间
3. **网络连接**: 需要稳定的网络连接访问外部API
4. **文件大小**: 建议单次处理不超过1000个创作者
5. **并发限制**: 同时只能处理一个分析任务

## 故障排除

### 常见问题

**1. API密钥错误**
- 检查`universal_brand_analyzer.py`中的API密钥配置
- 确保密钥有效且有足够的配额

**2. 上传失败**
- 检查文件格式是否为JSON
- 检查文件大小是否超过50MB限制

**3. 分析卡住**
- 检查网络连接
- 查看日志了解具体错误信息
- 重启应用重新尝试

**4. 结果不准确**
- 数据质量影响分析结果
- 可以调整分析器中的判断阈值

### 日志查看
应用运行时会在控制台显示详细日志，帮助诊断问题。

## 支持与反馈

如有问题或建议，请联系开发团队。

---

**版本**: v1.0.0  
**最后更新**: 2025年1月  
**作者**: Brand Analysis Team 
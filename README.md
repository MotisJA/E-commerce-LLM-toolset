# 基于LangChain的电商LLM工具集

一个基于 LangChain 的智能电商LLM代理系统，可以帮助用户寻找微博大V、生成营销方案和管理库存。

## 功能特点

- 大V搜索与分析
- 智能营销方案生成
- 库存管理与优化
- 客服聊天支持

## 环境要求

- Python 3.11
- 需要的主要依赖包见 requirements.txt

## 安装步骤

1. 克隆仓库
```bash
git clone [repository-url]
cd BiProj
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
复制 `.env.example` 文件为 `.env`，并填入必要的配置：
```
SERPAPI_API_KEY=your_serp_api_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=your_api_base_url
LLM_MODELEND=your_model_name
```

## 运行项目

1. 初始化数据库（首次运行需要）
```bash
python data/populate_inventory.py
```

2. 启动服务器
```bash
python app.py
```

3. 访问应用
打开浏览器访问 `http://localhost:5000`

## API 接口

### 1. 大V搜索
- 端点：`/process`
- 方法：POST
- 参数：flower (string)

### 2. 营销方案生成
- 端点：`/marketing/generate`
- 方法：POST
- 参数：product, target, goal (string)

### 3. 库存分析
- 端点：`/inventory/analyze`
- 方法：POST
- 参数：product, current_stock (string, number)

### 4. 客服聊天
- 端点：`/chat`
- 方法：POST
- 参数：message (string)

## 注意事项

- 确保所有环境变量都已正确配置
- 数据库文件会自动创建在 data 目录下
- 建议在生产环境中关闭调试模式

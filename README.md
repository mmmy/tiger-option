# Tiger Options Trading Service

一个基于Python + FastAPI的老虎证券期权交易微服务，实现了完整的TradingView信号接收和期权交易功能。

## 📋 功能特性

- ✅ **老虎API集成** - 集成tigeropen SDK，支持期权交易
- ✅ **Webhook信号接收** - 接收TradingView策略信号
- ✅ **多账户管理** - 支持多个老虎账户配置
- ✅ **期权交易策略** - 智能期权合约选择和下单
- ✅ **Mock模式** - 开发测试模式，无需真实交易
- ✅ **风险管理** - 完善的风险控制和仓位管理
- ✅ **数据持久化** - SQLite数据库存储交易记录
- ✅ **监控告警** - 完整的日志和监控系统

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- 老虎证券账户和API权限

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
复制并编辑配置文件：
```bash
cp config/apikeys.example.yml config/apikeys.yml
```

编辑 `config/apikeys.yml`，填入你的老虎API凭据。

### 4. 环境配置
创建 `.env` 文件：
```env
PORT=8000
USE_MOCK_MODE=true
DEBUG=true
```

### 5. 启动服务
```bash
# 开发模式
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 📡 API接口

### 核心接口
- **`POST /webhook/signal`** - TradingView webhook信号接收 (主要功能)
- **`GET /api/trading/status`** - 交易服务状态

### 系统接口
- **`GET /health`** - 健康检查
- **`GET /api/status`** - 服务状态
- **`GET /api/accounts`** - 获取账户信息
- **`GET /api/positions`** - 获取持仓信息

## 📁 项目结构

```
tiger-option/
├── src/                    # 源代码目录
│   ├── api/               # API接口层
│   ├── services/          # 业务服务层
│   ├── models/            # 数据模型
│   ├── utils/             # 工具函数
│   ├── config/            # 配置管理
│   ├── database/          # 数据库操作
│   ├── middleware/        # 中间件
│   └── main.py           # 主入口文件
├── config/                # 配置文件
├── tests/                 # 测试文件
├── docs/                  # 文档
├── logs/                  # 日志文件
├── data/                  # 数据文件
└── requirements.txt       # Python依赖
```

## 🔧 开发模式

项目支持Mock模式，在网络受限环境下可以进行开发测试：

1. 设置 `USE_MOCK_MODE=true` 在 `.env` 文件中
2. Mock模式会模拟所有老虎API响应
3. 支持完整的认证流程测试

## 🔐 安全说明

- API密钥文件 `config/apikeys.yml` 已加入 `.gitignore`
- 生产环境请设置适当的CORS配置
- 建议使用环境变量管理敏感信息

## 📚 老虎API文档

- [老虎开放平台官方文档](https://quant.itiger.com/openapi/)
- [tigeropen Python SDK](https://github.com/tigerfintech/openapi-python-sdk)

## 🎯 开发状态

- [x] 项目结构搭建
- [ ] 依赖管理配置
- [ ] 环境配置文件
- [ ] 基础类型定义
- [ ] 老虎API客户端
- [ ] Webhook接口开发
- [ ] 期权交易策略
- [ ] 数据库和持久化
- [ ] 监控和日志系统
- [ ] 测试和部署

## 📄 License

MIT

# VSCode 调试配置说明

## 📋 配置概述

已为Tiger Options Trading Service项目配置了完整的VSCode调试环境，包括：

- **调试配置** (`.vscode/launch.json`)
- **任务配置** (`.vscode/tasks.json`) 
- **编辑器设置** (`.vscode/settings.json`)
- **推荐扩展** (`.vscode/extensions.json`)
- **API测试文件** (`.vscode/api-test.http`)

## 🚀 调试配置说明

### 1. Debug Tiger Options Service
- **用途**: 直接调试主应用程序
- **启动方式**: 运行 `src/main.py`
- **适用场景**: 调试应用启动过程、配置加载等

### 2. Debug with Uvicorn ⭐ (推荐)
- **用途**: 使用Uvicorn调试Web服务
- **特点**: 支持热重载、详细日志
- **适用场景**: 调试API端点、Webhook处理等
- **端口**: 8000

### 3. Debug Test Script
- **用途**: 调试测试脚本
- **目标**: `test_account_chu.py`
- **适用场景**: 调试测试逻辑、API调用等

### 4. Debug Webhook Routes ⭐ (专用)
- **用途**: 专门调试Webhook相关功能
- **特点**: 启用DEBUG环境变量、自动清理进程
- **适用场景**: 调试 `src/api/webhook_routes.py` 等

### 5. Debug Current File
- **用途**: 调试当前打开的Python文件
- **适用场景**: 快速调试单个脚本

### 6. Attach to Running Server
- **用途**: 附加到正在运行的服务器进程
- **端口**: 5678 (需要在代码中添加debugpy)

## 🛠️ 使用方法

### 启动调试
1. 打开VSCode
2. 按 `F5` 或点击调试面板的"开始调试"
3. 选择合适的调试配置
4. 设置断点并开始调试

### 推荐调试流程
1. **启动服务**: 选择 "Debug with Uvicorn"
2. **设置断点**: 在 `src/api/webhook_routes.py` 中设置断点
3. **发送请求**: 使用 `.vscode/api-test.http` 发送测试请求
4. **调试分析**: 查看变量、调用栈等

## 📝 任务配置

### 可用任务 (Ctrl+Shift+P → "Tasks: Run Task")
- **Start Tiger Options Service**: 启动服务器
- **Run Tests**: 运行account_chu测试
- **Run All API Tests**: 运行所有API测试
- **Install Dependencies**: 安装依赖
- **Format Code**: 格式化代码

## 🔧 编辑器设置

### 已配置功能
- **Python解释器**: 自动检测
- **代码格式化**: Black (保存时自动格式化)
- **导入排序**: isort (保存时自动整理)
- **代码检查**: Flake8
- **类型检查**: Pylance (基础模式)
- **自动完成**: 启用
- **环境变量**: 自动设置PYTHONPATH

### 代码质量
- **行长度限制**: 100字符
- **自动去除尾随空格**: 启用
- **自动添加文件结尾换行**: 启用

## 🧩 推荐扩展

### 核心扩展
- **Python**: Python语言支持
- **Pylance**: Python语言服务器
- **Black Formatter**: 代码格式化
- **Flake8**: 代码检查
- **REST Client**: API测试

### 辅助扩展
- **GitLens**: Git增强
- **YAML**: YAML文件支持
- **Makefile Tools**: Makefile支持

## 🧪 API测试

### 使用REST Client
1. 打开 `.vscode/api-test.http`
2. 点击请求上方的 "Send Request"
3. 查看响应结果
4. 支持变量替换 (`{{baseUrl}}`, `{{accountName}}`)

### 测试场景
- ✅ 健康检查
- ✅ 账户管理
- ✅ 市场数据
- ✅ 交易功能
- ✅ Webhook信号
- ✅ 错误处理

## 🐛 调试技巧

### 1. 设置断点
```python
# 在关键位置设置断点
@router.post("/signal/{account_name}")
async def receive_signal(account_name: str, signal: WebhookSignal):
    # 在这里设置断点 ← 点击行号
    logger.info(f"Received signal for {account_name}")
```

### 2. 查看变量
- **局部变量**: 调试面板左侧
- **监视表达式**: 添加自定义表达式
- **调用栈**: 查看函数调用链

### 3. 条件断点
- 右键断点 → "编辑断点"
- 添加条件，如: `account_name == "account_chu"`

### 4. 日志断点
- 右键断点 → "编辑断点"
- 选择"日志消息"而不是"中断"

## 🔍 常见调试场景

### 调试Webhook处理
1. 启动 "Debug Webhook Routes"
2. 在 `webhook_routes.py` 的 `receive_signal` 函数设置断点
3. 使用REST Client发送POST请求到 `/webhook/signal/account_chu`
4. 查看信号处理流程

### 调试账户连接
1. 在 `auth_service.py` 的 `test_connection` 方法设置断点
2. 发送GET请求到 `/api/accounts/account_chu/test-connection`
3. 查看连接测试过程

### 调试市场数据
1. 在 `market_routes.py` 设置断点
2. 发送GET请求到 `/api/market/search/AAPL`
3. 查看数据获取和处理过程

## 📚 快捷键

- **F5**: 开始调试
- **F9**: 切换断点
- **F10**: 单步跳过
- **F11**: 单步进入
- **Shift+F11**: 单步跳出
- **Ctrl+Shift+F5**: 重启调试
- **Shift+F5**: 停止调试

## 🎯 调试最佳实践

1. **先设置断点再启动调试**
2. **使用条件断点减少不必要的中断**
3. **利用日志断点输出调试信息**
4. **结合REST Client测试API端点**
5. **查看调用栈了解代码执行路径**
6. **使用监视表达式跟踪关键变量**

---

现在您可以开始使用VSCode进行高效的调试了！🎉

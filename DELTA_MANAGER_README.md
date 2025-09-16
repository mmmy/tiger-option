# 🐅 Tiger期权Delta管理器

## 概述

Tiger期权Delta管理器是一个基于Web的管理界面，用于监控和管理Tiger期权交易账户的Delta风险。该界面完全按照deribit_webhook项目的delta-manager.html设计，但专门适配了Tiger期权交易的特点。

## 功能特性

### 📊 实时数据监控
- **账户摘要**：显示账户余额、可用资金、总Delta等关键指标
- **期权仓位**：实时显示所有期权仓位的详细信息
- **未成交订单**：监控所有未成交的期权订单
- **交易记录**：查看最近的期权交易历史

### 🎯 Delta风险管理
- **总Delta统计**：实时计算和显示账户总Delta风险
- **仓位Delta分析**：按合约显示Delta值和风险敞口
- **颜色编码**：正Delta显示绿色，负Delta显示红色

### 🔧 交易操作
- **一键平仓**：快速平仓指定期权合约
- **订单撤销**：取消未成交的期权订单
- **实时刷新**：手动刷新各类数据

### 📋 TradingView集成
- **警报消息模板**：生成TradingView webhook消息模板
- **自动复制**：一键复制警报消息到剪贴板
- **账户自适应**：根据选择的账户自动生成对应的消息模板

## 使用方法

### 1. 启动服务
```bash
# 启动Tiger期权交易服务
python test_server.py
```

### 2. 访问管理界面
打开浏览器访问：
```
http://localhost:8000/static/delta-manager.html
```

### 3. 选择账户
1. 在页面顶部的下拉菜单中选择要管理的账户
2. 系统会自动加载该账户的所有数据

### 4. 监控Delta风险
- 查看顶部统计卡片中的总Delta和仓位Delta
- 在仓位表格中查看每个合约的详细Delta信息
- 使用颜色编码快速识别风险方向

### 5. 执行交易操作
- 点击"平仓"按钮快速平仓指定合约
- 点击"撤单"按钮取消未成交订单
- 使用各个"刷新"按钮更新最新数据

### 6. 生成TradingView警报
1. 选择要使用的账户
2. 点击"📋 复制警报消息"按钮
3. 系统会生成并复制警报消息模板到剪贴板
4. 在TradingView中粘贴使用

## API端点

Delta管理器使用以下API端点获取数据：

### 账户管理
- `GET /api/accounts` - 获取账户列表
- `GET /api/accounts/{account_name}/summary` - 获取账户摘要
- `GET /api/accounts/{account_name}/positions` - 获取期权仓位
- `GET /api/accounts/{account_name}/orders` - 获取未成交订单
- `GET /api/accounts/{account_name}/trades` - 获取交易记录

### 交易操作
- `POST /api/accounts/{account_name}/orders/{order_id}/cancel` - 撤销订单
- `POST /api/accounts/{account_name}/positions/{symbol}/close` - 平仓

## 技术特点

### 🎨 界面设计
- **Tiger主题**：使用Tiger品牌橙色配色方案
- **响应式设计**：支持桌面和移动设备
- **现代化UI**：采用渐变背景和卡片式布局

### ⚡ 性能优化
- **并行加载**：同时加载多个数据源
- **智能刷新**：支持单独刷新各个数据模块
- **错误处理**：完善的错误提示和重试机制

### 🔒 安全性
- **账户验证**：确保只能访问有效的账户
- **操作确认**：重要操作需要用户确认
- **错误边界**：防止单个错误影响整个界面

## 开发说明

### 文件结构
```
public/
├── delta-manager.html          # 主界面文件
src/api/
├── account_routes.py           # 账户管理API路由
src/services/
├── mock_tiger_client.py        # Mock客户端（包含新增方法）
```

### 扩展功能
如需添加新功能，可以：
1. 在`account_routes.py`中添加新的API端点
2. 在`mock_tiger_client.py`中添加对应的mock方法
3. 在`delta-manager.html`中添加前端界面和逻辑

## 注意事项

1. **Mock模式**：当前运行在Mock模式下，所有数据都是模拟数据
2. **生产环境**：在生产环境中需要配置真实的Tiger API密钥
3. **网络延迟**：实际使用中可能存在网络延迟，界面已做相应优化
4. **数据刷新**：建议定期刷新数据以获取最新信息

## 故障排除

### 常见问题
1. **页面无法加载**：检查服务器是否正常启动
2. **数据显示为空**：检查账户配置是否正确
3. **操作失败**：查看浏览器控制台和服务器日志

### 调试方法
1. 打开浏览器开发者工具查看网络请求
2. 检查服务器终端输出的错误信息
3. 使用`test_delta_manager_api.py`测试API端点

---

🎉 **恭喜！** 您现在拥有了一个功能完整的Tiger期权Delta管理器，可以有效监控和管理期权交易风险！

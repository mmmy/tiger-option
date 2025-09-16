# 📋 Webhook Payload 详细类型定义

## 🎯 概述

Tiger Options Trading Service 的 webhook payload 使用了详细的 Pydantic 类型定义，完全兼容 deribit_webhook 项目的格式。

## 📝 WebhookSignalPayload 类型定义

### 🔧 基本信息字段

```python
class WebhookSignalPayload(BaseModel):
    # 账户和交易信息
    account_name: str = Field(
        alias="accountName",
        description="账户名称，对应 apikeys 配置中的名称"
    )
    
    side: Literal["buy", "sell"] = Field(
        description="交易方向：买入/卖出"
    )
    
    exchange: str = Field(
        description="交易所名称"
    )
    
    period: str = Field(
        description="K线周期"
    )
```

### 📊 市场仓位信息

```python
    # 市场仓位信息
    market_position: Literal["long", "short", "flat"] = Field(
        alias="marketPosition",
        description="当前市场仓位"
    )
    
    prev_market_position: Literal["long", "short", "flat"] = Field(
        alias="prevMarketPosition", 
        description="之前的市场仓位"
    )
```

### 💰 交易详情

```python
    # 交易详情
    symbol: str = Field(description="交易对符号")
    price: str = Field(description="当前价格")
    timestamp: str = Field(description="时间戳")
    size: str = Field(description="订单数量/合约数")
    position_size: str = Field(
        alias="positionSize",
        description="当前仓位大小"
    )
```

### 🆔 订单标识

```python
    # 订单标识
    id: str = Field(description="策略订单ID")
    alert_message: Optional[str] = Field(
        default=None,
        alias="alertMessage",
        description="警报消息"
    )
    comment: Optional[str] = Field(default=None, description="备注")
```

### 📏 数量类型

```python
    # 数量类型
    qty_type: Literal["fixed", "cash"] = Field(
        alias="qtyType",
        description="数量类型：固定数量或现金金额"
    )
```

### 📺 TradingView 特定字段

```python
    # TradingView 特定字段
    tv_id: Optional[int] = Field(default=None, description="TradingView信号ID")
```

### 🎯 期权交易专用字段

```python
    # 期权交易的可选 delta 字段
    delta1: Optional[float] = Field(
        default=None, 
        description="开仓时的期权Delta值"
    )
    
    n: Optional[int] = Field(
        default=None, 
        description="期权选择的最小到期天数"
    )
    
    delta2: Optional[float] = Field(
        default=None, 
        description="记录到delta数据库的目标Delta值"
    )
```

## ✅ 数据验证

### 🔢 数值字符串验证

```python
@validator('price', 'size', 'position_size')
def validate_numeric_strings(cls, v):
    """验证数值字符串可以转换为 Decimal"""
    try:
        Decimal(v)
        return v
    except Exception:
        raise ValueError(f"Invalid numeric value: {v}")
```

### ⏰ 时间戳验证

```python
@validator('timestamp')
def validate_timestamp(cls, v):
    """验证时间戳格式"""
    try:
        # 尝试解析为 ISO 格式或 Unix 时间戳
        if v.isdigit():
            datetime.fromtimestamp(int(v))
        else:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    except Exception:
        raise ValueError(f"Invalid timestamp format: {v}")
```

## 🛠️ 便利属性

### 💰 数值转换属性

```python
@property
def price_decimal(self) -> Decimal:
    """获取价格的 Decimal 类型"""
    return Decimal(self.price)

@property
def size_decimal(self) -> Decimal:
    """获取数量的 Decimal 类型"""
    return Decimal(self.size)

@property
def position_size_decimal(self) -> Decimal:
    """获取仓位大小的 Decimal 类型"""
    return Decimal(self.position_size)

@property
def timestamp_datetime(self) -> datetime:
    """获取时间戳的 datetime 类型"""
    if self.timestamp.isdigit():
        return datetime.fromtimestamp(int(self.timestamp))
    else:
        return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
```

### 📊 仓位状态判断属性

```python
@property
def is_opening_position(self) -> bool:
    """检查是否为开仓信号"""
    return self.prev_market_position == "flat" and self.market_position != "flat"

@property
def is_closing_position(self) -> bool:
    """检查是否为平仓信号"""
    return self.prev_market_position != "flat" and self.market_position == "flat"

@property
def is_reversing_position(self) -> bool:
    """检查是否为反转仓位信号"""
    return (
        self.prev_market_position != "flat" and 
        self.market_position != "flat" and 
        self.prev_market_position != self.market_position
    )
```

## 📋 完整示例载荷

```json
{
  "accountName": "account_1",
  "side": "buy",
  "exchange": "TIGER",
  "period": "1h",
  "marketPosition": "long",
  "prevMarketPosition": "flat",
  "symbol": "AAPL",
  "price": "150.50",
  "timestamp": "2025-09-09T21:30:00Z",
  "size": "10",
  "positionSize": "0",
  "id": "test_signal_001",
  "qtyType": "fixed",
  "alertMessage": "Test signal from TradingView",
  "comment": "Opening AAPL long position",
  "tv_id": 12345,
  "delta1": 0.5,
  "n": 30,
  "delta2": 0.6
}
```

## 🎯 字段映射

| JSON字段 | Python属性 | 类型 | 必需 | 描述 |
|----------|------------|------|------|------|
| `accountName` | `account_name` | `str` | ✅ | 账户名称 |
| `side` | `side` | `"buy"\|"sell"` | ✅ | 交易方向 |
| `exchange` | `exchange` | `str` | ✅ | 交易所 |
| `period` | `period` | `str` | ✅ | K线周期 |
| `marketPosition` | `market_position` | `"long"\|"short"\|"flat"` | ✅ | 当前仓位 |
| `prevMarketPosition` | `prev_market_position` | `"long"\|"short"\|"flat"` | ✅ | 之前仓位 |
| `symbol` | `symbol` | `str` | ✅ | 交易符号 |
| `price` | `price` | `str` | ✅ | 价格 |
| `timestamp` | `timestamp` | `str` | ✅ | 时间戳 |
| `size` | `size` | `str` | ✅ | 数量 |
| `positionSize` | `position_size` | `str` | ✅ | 仓位大小 |
| `id` | `id` | `str` | ✅ | 订单ID |
| `qtyType` | `qty_type` | `"fixed"\|"cash"` | ✅ | 数量类型 |
| `alertMessage` | `alert_message` | `str?` | ❌ | 警报消息 |
| `comment` | `comment` | `str?` | ❌ | 备注 |
| `tv_id` | `tv_id` | `int?` | ❌ | TradingView ID |
| `delta1` | `delta1` | `float?` | ❌ | 开仓Delta |
| `n` | `n` | `int?` | ❌ | 最小到期天数 |
| `delta2` | `delta2` | `float?` | ❌ | 目标Delta |

## 🚀 使用优势

1. **🔒 类型安全**：编译时类型检查，减少运行时错误
2. **📝 自动文档**：FastAPI 自动生成 OpenAPI 文档
3. **✅ 数据验证**：自动验证输入数据格式和类型
4. **🔄 自动转换**：JSON 字段名自动映射到 Python 属性
5. **💡 IDE 支持**：完整的代码补全和类型提示
6. **🛡️ 错误处理**：详细的验证错误信息

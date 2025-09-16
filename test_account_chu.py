#!/usr/bin/env python3
"""
Test script specifically for account_chu (模拟盘账户)
"""

import json
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
ACCOUNT_NAME = "account_chu"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def test_server_health():
    """Test if server is running"""
    print_section("服务器健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def test_account_list():
    """Test account list endpoint"""
    print_section("账户列表检查")
    
    try:
        response = requests.get(f"{BASE_URL}/api/accounts", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取账户列表")
            
            if data.get('success') and 'data' in data:
                accounts = data['data']
                print(f"发现 {len(accounts)} 个账户:")
                
                for account in accounts:
                    if isinstance(account, dict):
                        name = account.get('name', 'Unknown')
                        enabled = account.get('enabled', False)
                        description = account.get('description', 'No description')
                        status = "启用" if enabled else "禁用"
                        print(f"  - {name}: {description} ({status})")

                        if name == ACCOUNT_NAME:
                            print(f"    ✅ 找到目标账户: {ACCOUNT_NAME}")
                            return True
                    else:
                        # Handle case where account is a string (account name only)
                        print(f"  - {account}: (简化格式)")
                        if account == ACCOUNT_NAME:
                            print(f"    ✅ 找到目标账户: {ACCOUNT_NAME}")
                            return True
                
                print(f"❌ 未找到账户: {ACCOUNT_NAME}")
                return False
            else:
                print("❌ 响应数据格式异常")
                return False
        else:
            print(f"❌ 获取账户列表失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 账户列表检查失败: {e}")
        return False

def test_account_connection():
    """Test account connection"""
    print_section("账户连接测试")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/accounts/{ACCOUNT_NAME}/test-connection", 
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 连接测试请求成功")
            
            if data.get('success'):
                print("✅ 账户连接正常")
                connection_data = data.get('data', {})
                print(f"  - 账户名称: {connection_data.get('account_name')}")
                print(f"  - 连接状态: {connection_data.get('connection_status')}")
                print(f"  - 测试时间: {connection_data.get('test_timestamp')}")
                print(f"  - 账户信息可用: {connection_data.get('account_info_available')}")
                return True
            else:
                print("❌ 账户连接失败")
                connection_data = data.get('data', {})
                print(f"  - 错误信息: {connection_data.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 连接测试失败: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False

def test_account_info():
    """Test getting account information"""
    print_section("账户信息获取")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/accounts/{ACCOUNT_NAME}/info", 
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取账户信息")
            
            if data.get('success') and 'data' in data:
                account_info = data['data']
                print("账户详细信息:")
                print(f"  - 账户号码: {account_info.get('account')}")
                print(f"  - 货币: {account_info.get('currency')}")

                # Handle potential string values for numeric fields
                buying_power = account_info.get('buying_power', 0)
                cash = account_info.get('cash', 0)
                market_value = account_info.get('market_value', 0)
                net_liquidation = account_info.get('net_liquidation', 0)

                # Convert to float if they are strings
                try:
                    buying_power = float(buying_power) if buying_power else 0
                    cash = float(cash) if cash else 0
                    market_value = float(market_value) if market_value else 0
                    net_liquidation = float(net_liquidation) if net_liquidation else 0
                except (ValueError, TypeError):
                    buying_power = cash = market_value = net_liquidation = 0

                print(f"  - 购买力: ${buying_power:,.2f}")
                print(f"  - 现金: ${cash:,.2f}")
                print(f"  - 市值: ${market_value:,.2f}")
                print(f"  - 净清算价值: ${net_liquidation:,.2f}")
                return True
            else:
                print("❌ 账户信息数据格式异常")
                return False
        else:
            print(f"❌ 获取账户信息失败: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"❌ 获取账户信息异常: {e}")
        return False

def test_account_summary():
    """Test getting account summary"""
    print_section("账户摘要信息")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/trading/account/{ACCOUNT_NAME}/summary", 
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取账户摘要")
            
            if data.get('success') and 'data' in data:
                summary = data['data']
                print("账户摘要信息:")
                print(f"  - 账户名称: {summary.get('account_name')}")
                print(f"  - 净清算价值: ${summary.get('net_liquidation', 0):,.2f}")
                print(f"  - 总现金: ${summary.get('total_cash', 0):,.2f}")
                print(f"  - 可用资金: ${summary.get('available_funds', 0):,.2f}")
                print(f"  - 购买力: ${summary.get('buying_power', 0):,.2f}")
                print(f"  - 总Delta: {summary.get('total_delta', 0):.4f}")
                print(f"  - 持仓Delta: {summary.get('position_delta', 0):.4f}")
                print(f"  - 持仓数量: {summary.get('position_count', 0)}")
                return True
            else:
                print("❌ 账户摘要数据格式异常")
                return False
        else:
            print(f"❌ 获取账户摘要失败: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"❌ 获取账户摘要异常: {e}")
        return False

def test_market_data():
    """Test market data access"""
    print_section("市场数据测试")
    
    try:
        # Test symbol search
        response = requests.get(
            f"{BASE_URL}/api/market/search/AAPL?account_name={ACCOUNT_NAME}&limit=3", 
            timeout=30
        )
        
        print(f"AAPL搜索响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取市场数据")
            
            if data.get('success') and 'data' in data:
                results = data['data']
                print(f"找到 {len(results)} 个AAPL相关合约:")
                
                for i, contract in enumerate(results[:3]):  # Show first 3
                    print(f"  {i+1}. {contract.get('symbol', 'N/A')} - {contract.get('name', 'N/A')}")
                    print(f"     类型: {contract.get('sec_type', 'N/A')}")
                    if contract.get('last_price'):
                        print(f"     最新价格: ${contract.get('last_price')}")
                
                return True
            else:
                print("❌ 市场数据格式异常")
                return False
        else:
            print(f"❌ 获取市场数据失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 市场数据测试异常: {e}")
        return False

def test_simple_webhook():
    """Test a simple webhook signal"""
    print_section("简单交易信号测试")
    
    signal_data = {
        "signal_id": f"test_chu_{int(time.time())}",
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 1,
        "price": 150.00,
        "order_type": "limit",
        "time_in_force": "day",
        "strategy": "account_chu_test",
        "comment": "account_chu账户测试信号"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/signal/{ACCOUNT_NAME}",
            json=signal_data,
            timeout=30
        )
        
        print(f"信号发送响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 交易信号发送成功")
            
            if data.get('success'):
                signal_info = data.get('data', {})
                print(f"  - 信号ID: {signal_info.get('signal_id')}")
                print(f"  - 处理状态: {signal_info.get('status', '未知')}")
                print(f"  - 处理时间: {signal_info.get('timestamp')}")
                return True
            else:
                print("❌ 信号处理失败")
                print(f"错误信息: {data.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 信号发送失败: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            return False
            
    except Exception as e:
        print(f"❌ 交易信号测试异常: {e}")
        return False

def main():
    """Run comprehensive tests for account_chu"""
    
    print("=== account_chu 模拟盘账户测试 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标账户: {ACCOUNT_NAME}")
    print(f"服务器地址: {BASE_URL}")
    
    # Run all tests
    tests = [
        ("服务器健康检查", test_server_health),
        ("账户列表检查", test_account_list),
        ("账户连接测试", test_account_connection),
        ("账户信息获取", test_account_info),
        ("账户摘要信息", test_account_summary),
        ("市场数据测试", test_market_data),
        ("简单交易信号测试", test_simple_webhook),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_section("测试结果汇总")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 account_chu账户测试全部通过！账户状态正常。")
    else:
        print("⚠️  部分测试失败，请检查账户配置和服务器状态。")
    
    return passed == total

if __name__ == "__main__":
    main()

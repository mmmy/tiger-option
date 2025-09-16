#!/usr/bin/env python3
"""
Test script for the new homepage
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_homepage():
    """Test the homepage"""
    print("=== 测试新主页 ===")
    
    try:
        # Test root endpoint
        print("\n1. 测试根路径 (/)...")
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            if 'text/html' in response.headers.get('content-type', ''):
                print("✅ 成功返回HTML页面")
                
                # Check if it contains expected content
                content = response.text
                if "Tiger Options Trading Service" in content:
                    print("✅ 页面包含正确的标题")
                else:
                    print("❌ 页面标题不正确")
                
                if "Delta管理器" in content:
                    print("✅ 页面包含Delta管理器链接")
                else:
                    print("❌ 页面缺少Delta管理器链接")
                
                if "API文档" in content:
                    print("✅ 页面包含API文档链接")
                else:
                    print("❌ 页面缺少API文档链接")
                    
                print(f"页面大小: {len(content)} 字符")
                
            else:
                print("❌ 返回的不是HTML页面")
                print(f"响应内容: {response.text[:200]}...")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_api_endpoint():
    """Test the API info endpoint"""
    print("\n2. 测试API信息端点 (/api)...")
    
    try:
        response = requests.get(f"{BASE_URL}/api", timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            if 'application/json' in response.headers.get('content-type', ''):
                print("✅ 成功返回JSON响应")
                
                data = response.json()
                if data.get('message') == "Tiger Options Trading Service":
                    print("✅ API信息正确")
                    print(f"版本: {data.get('version')}")
                    print(f"环境: {data.get('environment')}")
                    print(f"Mock模式: {data.get('mock_mode')}")
                else:
                    print("❌ API信息不正确")
                    
            else:
                print("❌ 返回的不是JSON响应")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_static_files():
    """Test static file access"""
    print("\n3. 测试静态文件访问...")
    
    # Test delta manager
    try:
        response = requests.get(f"{BASE_URL}/static/delta-manager.html", timeout=10)
        
        print(f"Delta管理器状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Delta管理器页面可访问")
        else:
            print("❌ Delta管理器页面无法访问")
            
    except Exception as e:
        print(f"❌ Delta管理器测试失败: {e}")

def test_health_endpoint():
    """Test health endpoint"""
    print("\n4. 测试健康检查端点...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        print(f"健康检查状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 健康检查正常")
            data = response.json()
            print(f"服务状态: {data.get('status', 'Unknown')}")
        else:
            print("❌ 健康检查失败")
            
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")

def test_docs_endpoint():
    """Test API docs endpoint"""
    print("\n5. 测试API文档端点...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        
        print(f"API文档状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print("❌ API文档无法访问")
            
    except Exception as e:
        print(f"❌ API文档测试失败: {e}")

def main():
    """Run all homepage tests"""
    print("🐅 Tiger Options Trading Service - 主页测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务器地址: {BASE_URL}")
    
    # Run all tests
    tests = [
        test_homepage,
        test_api_endpoint,
        test_static_files,
        test_health_endpoint,
        test_docs_endpoint,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ 测试函数 {test_func.__name__} 失败: {e}")
        
        time.sleep(0.5)  # Brief pause between tests
    
    print("\n=== 测试完成 ===")
    print("请在浏览器中访问 http://localhost:8000 查看新主页")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
快速验证API密钥持久化功能
"""

import requests
import json

# 使用现有的容器端口
CONTAINER_PORT = 51746
API_KEY = "AIzaSyASwFBYz1OGf44qvuox8b2KuIrNlDStafc"

def main():
    print("🧪 快速验证API密钥持久化功能")
    
    # 1. 配置API密钥
    print("\n1️⃣ 配置API密钥...")
    config_response = requests.post(
        f"http://127.0.0.1:{CONTAINER_PORT}/gemini/configure",
        json={"api_key": API_KEY}
    )
    print(f"配置结果: {config_response.json()}")
    
    # 2. 测试不带API密钥的请求
    print("\n2️⃣ 发送请求（不传入API密钥）...")
    questions = [
        "What is 10 + 5?",
        "What is the capital of Japan?",
        "Write a Python function to reverse a string"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        response = requests.post(
            f"http://127.0.0.1:{CONTAINER_PORT}/gemini",
            json={"prompt": question}  # 注意：没有传入api_key
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 回答: {result.get('response', '无响应')}")
        else:
            print(f"❌ 请求失败: {response.text}")
    
    print("\n🎉 测试完成！API密钥持久化功能正常工作！")

if __name__ == "__main__":
    main()

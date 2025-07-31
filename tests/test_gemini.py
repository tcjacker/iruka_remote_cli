#!/usr/bin/env python3
"""
测试脚本：演示如何使用Gemini CLI集成
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import load_env_file, get_config

# Load configuration
load_env_file()
config = get_config()

# 主服务地址
MAIN_SERVICE_URL = config.get_main_service_url()

def create_environment():
    """创建一个新的环境"""
    print("Creating new environment...")
    response = requests.post(f"{MAIN_SERVICE_URL}/environments")
    if response.status_code == 201:
        env_data = response.json()
        env_id = env_data['env_id']
        print(f"Environment created successfully: {env_id}")
        return env_id
    else:
        print(f"Failed to create environment: {response.text}")
        return None

def check_gemini_status(env_id):
    """检查Gemini CLI状态"""
    print(f"Checking Gemini status in environment {env_id}...")
    response = requests.get(f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini/status")
    if response.status_code == 200:
        status = response.json()
        print(f"Gemini status: {status}")
        return status
    else:
        print(f"Failed to check Gemini status: {response.text}")
        return None

def send_gemini_prompt(env_id, prompt):
    """发送提示到Gemini CLI"""
    print(f"Sending prompt to Gemini in environment {env_id}...")
    print(f"Prompt: {prompt}")
    
    response = requests.post(
        f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini",
        json={"prompt": prompt}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Gemini response: {result.get('response', 'No response')}")
        return result
    else:
        print(f"Failed to send prompt: {response.text}")
        return None

def restart_gemini(env_id):
    """重启Gemini CLI"""
    print(f"Restarting Gemini in environment {env_id}...")
    response = requests.post(f"{MAIN_SERVICE_URL}/environments/{env_id}/gemini/restart")
    if response.status_code == 200:
        result = response.json()
        print(f"Restart result: {result}")
        return result
    else:
        print(f"Failed to restart Gemini: {response.text}")
        return None

def delete_environment(env_id):
    """删除环境"""
    print(f"Deleting environment {env_id}...")
    response = requests.delete(f"{MAIN_SERVICE_URL}/environments/{env_id}")
    if response.status_code == 200:
        print("Environment deleted successfully")
        return True
    else:
        print(f"Failed to delete environment: {response.text}")
        return False

def main():
    """主测试函数"""
    print("=== Gemini CLI Integration Test ===")
    
    # 1. 创建环境
    env_id = create_environment()
    if not env_id:
        return
    
    # 等待容器启动
    print("Waiting for container to start...")
    time.sleep(10)
    
    try:
        # 2. 检查Gemini状态
        check_gemini_status(env_id)
        
        # 3. 发送测试提示
        test_prompts = [
            "Hello, how are you?",
            "What is Python?",
            "Tell me a joke"
        ]
        
        for prompt in test_prompts:
            print(f"\n--- Testing prompt: {prompt} ---")
            send_gemini_prompt(env_id, prompt)
            time.sleep(2)  # 等待响应
        
        # 4. 重启Gemini（可选）
        print(f"\n--- Testing Gemini restart ---")
        restart_gemini(env_id)
        time.sleep(5)
        
        # 5. 再次检查状态
        check_gemini_status(env_id)
        
    finally:
        # 6. 清理环境
        print(f"\n--- Cleaning up ---")
        delete_environment(env_id)

if __name__ == "__main__":
    main()

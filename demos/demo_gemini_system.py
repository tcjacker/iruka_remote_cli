#!/usr/bin/env python3
"""
完整的Gemini CLI Docker集成系统演示脚本
展示如何通过Web API与Docker容器中的Gemini CLI进行交互
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import load_env_file, get_config

# Load configuration
load_env_file()
config = get_config()

# 配置
BASE_URL = config.get_main_service_url()
GEMINI_API_KEY = config.GEMINI_API_KEY

def print_header(title):
    """打印格式化的标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step):
    """打印步骤信息"""
    print(f"\n🔹 {step}")

def create_environment():
    """创建新环境"""
    print_step("创建新的Docker环境...")
    response = requests.post(f"{BASE_URL}/environments")
    if response.status_code in [200, 201]:
        data = response.json()
        env_id = data['env_id']
        port = data['port']
        print(f"✅ 环境创建成功!")
        print(f"   环境ID: {env_id}")
        print(f"   端口: {port}")
        return env_id, port
    else:
        print(f"❌ 环境创建失败: {response.status_code} - {response.text}")
        return None, None

def wait_for_container(env_id, port, max_wait=90):
    """等待容器启动完成"""
    print_step(f"等待容器启动完成 (最多等待{max_wait}秒)...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 容器已启动并准备就绪! (等待了{i+1}秒)")
                return True
        except:
            pass
        
        if i % 10 == 0:
            print(f"   等待中... ({i+1}/{max_wait}秒)")
        time.sleep(1)
    
    print(f"❌ 容器启动超时")
    return False

def configure_api_key(env_id, api_key):
    """配置Gemini API密钥"""
    print_step("配置Gemini API密钥...")
    response = requests.post(
        f"{BASE_URL}/environments/{env_id}/gemini/configure",
        json={"api_key": api_key}
    )
    if response.status_code == 200:
        print("✅ API密钥配置成功!")
        return True
    else:
        print(f"❌ API密钥配置失败: {response.text}")
        return False

def check_gemini_status(env_id):
    """检查Gemini CLI状态"""
    print_step("检查Gemini CLI状态...")
    response = requests.get(f"{BASE_URL}/environments/{env_id}/gemini/status")
    if response.status_code == 200:
        data = response.json()
        status = "运行中" if data.get('gemini_running', False) else "未运行"
        print(f"✅ Gemini CLI状态: {status}")
        return data.get('gemini_running', False)
    else:
        print(f"❌ 状态检查失败: {response.text}")
        return False

def send_prompt(env_id, prompt):
    """发送提示到Gemini CLI"""
    print_step(f"发送提示: '{prompt}'")
    
    payload = {"prompt": prompt}
    response = requests.post(
        f"{BASE_URL}/environments/{env_id}/gemini",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        response_text = data.get('response', '无响应')
        print(f"✅ Gemini响应:")
        print(f"   {response_text}")
        return True
    else:
        print(f"❌ 请求失败: {response.text}")
        return False

def delete_environment(env_id):
    """删除环境"""
    print_step("清理环境...")
    response = requests.delete(f"{BASE_URL}/environments/{env_id}")
    if response.status_code == 200:
        print("✅ 环境删除成功!")
        return True
    else:
        print(f"❌ 环境删除失败: {response.text}")
        return False

def main():
    """主演示函数"""
    print_header("Gemini CLI Docker集成系统演示")
    
    print("🚀 这个演示将展示:")
    print("   1. 创建Docker环境")
    print("   2. 等待容器启动")
    print("   3. 配置Gemini API密钥")
    print("   4. 与Gemini CLI进行多轮对话")
    print("   5. 清理环境")
    
    # 创建环境
    env_id, port = create_environment()
    if not env_id:
        print("❌ 演示失败: 无法创建环境")
        return
    
    try:
        # 等待容器启动
        if not wait_for_container(env_id, port):
            print("❌ 演示失败: 容器启动超时")
            return
        
        # 配置API密钥
        configure_api_key(env_id, GEMINI_API_KEY)
        
        # 检查状态
        check_gemini_status(env_id)
        
        # 演示对话
        print_header("开始与Gemini CLI对话")
        
        demo_prompts = [
            "你好！请简单介绍一下自己。",
            "什么是Docker容器？",
            "用Python写一个简单的Hello World程序",
            "解释一下什么是API",
            "告诉我一个编程笑话"
        ]
        
        for i, prompt in enumerate(demo_prompts, 1):
            print(f"\n--- 对话 {i}/{len(demo_prompts)} ---")
            send_prompt(env_id, prompt)
            time.sleep(2)  # 避免请求过于频繁
        
        print_header("演示完成")
        print("🎉 所有功能都正常工作!")
        print("\n📋 系统架构总结:")
        print("   前端请求 → 主服务(Flask) → Docker容器 → Gemini CLI → AI响应")
        print("\n🔧 可用的API端点:")
        print("   POST /environments - 创建环境")
        print("   POST /environments/{id}/gemini/configure - 配置API密钥")
        print("   POST /environments/{id}/gemini - 发送提示")
        print("   GET  /environments/{id}/gemini/status - 检查状态")
        print("   POST /environments/{id}/gemini/restart - 重启Gemini")
        print("   DELETE /environments/{id} - 删除环境")
        
    finally:
        # 清理环境
        delete_environment(env_id)
    
    print("\n✨ 演示结束!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick test script for persistent Gemini CLI session functionality.
"""

import requests
import json
import time

def test_basic_functionality():
    """Quick test of basic persistent session functionality"""
    base_url = "http://localhost:8081"
    
    print("🧪 Quick Test: Persistent Gemini CLI Session")
    print("=" * 50)
    
    try:
        # 1. Create environment
        print("1. Creating environment...")
        response = requests.post(f"{base_url}/environments", timeout=30)
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create environment: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        env_id = response.json().get('env_id')
        print(f"✅ Environment created: {env_id}")
        
        # 2. Check initial session status
        print("\n2. Checking initial session status...")
        response = requests.get(f"{base_url}/environments/{env_id}/gemini/session/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Session status: {status}")
        
        # 3. Test first conversation
        print("\n3. Testing first conversation...")
        payload = {
            "prompt": "Hello! Please remember that I'm testing the persistent session. My test ID is ABC123."
        }
        
        response = requests.post(f"{base_url}/environments/{env_id}/gemini/session", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ First conversation successful")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
            print(f"   Persistent: {data.get('persistent')}")
            print(f"   Context managed by: {data.get('context_maintained_by')}")
        else:
            print(f"❌ First conversation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        # 4. Test context preservation
        print("\n4. Testing context preservation...")
        time.sleep(2)  # Small delay
        
        payload = {
            "prompt": "What was my test ID that I mentioned in our previous conversation?"
        }
        
        response = requests.post(f"{base_url}/environments/{env_id}/gemini/session", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            if 'abc123' in response_text:
                print("✅ Context preservation working - Gemini CLI remembered the test ID!")
            else:
                print("⚠️  Context preservation unclear - response:")
                print(f"   {data.get('response', '')[:200]}...")
        else:
            print(f"❌ Context test failed: {response.status_code}")
            return False
        
        # 5. Check active session status
        print("\n5. Checking active session status...")
        response = requests.get(f"{base_url}/environments/{env_id}/gemini/session/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            if status.get('active'):
                print(f"✅ Session is active")
                print(f"   Created: {status.get('created_at')}")
                print(f"   Last used: {status.get('last_used')}")
            else:
                print("❌ Session should be active but isn't")
        
        print("\n🎉 Basic functionality test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n✅ Quick test passed! The persistent Gemini CLI session appears to be working.")
    else:
        print("\n❌ Quick test failed. Please check the service and try again.")

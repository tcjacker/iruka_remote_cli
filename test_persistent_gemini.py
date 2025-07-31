#!/usr/bin/env python3
"""
Test script for persistent Gemini CLI session functionality.

This script tests:
1. Creating and connecting to persistent Gemini CLI sessions
2. Multi-turn conversation with context preservation
3. Session status and management
4. Error handling and recovery

Usage:
    python test_persistent_gemini.py [--api-key YOUR_API_KEY]
"""

import requests
import json
import time
import sys
import argparse
from typing import Dict, Any, Optional

class GeminiSessionTester:
    def __init__(self, base_url: str = "http://localhost:8081", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.env_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def create_environment(self) -> bool:
        """Test: Create a new environment"""
        try:
            response = requests.post(f"{self.base_url}/environments", timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.env_id = data.get('env_id')
                self.log_test("Create Environment", True, f"Environment ID: {self.env_id}")
                return True
            else:
                self.log_test("Create Environment", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Environment", False, f"Exception: {str(e)}")
            return False
    
    def test_session_status_empty(self) -> bool:
        """Test: Check session status when no session exists"""
        try:
            response = requests.get(f"{self.base_url}/environments/{self.env_id}/gemini/session/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data.get('active', True):  # Should be False when no session
                    self.log_test("Session Status (Empty)", True, "No active session detected correctly")
                    return True
                else:
                    self.log_test("Session Status (Empty)", False, "Unexpected active session")
                    return False
            else:
                self.log_test("Session Status (Empty)", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Status (Empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_first_conversation(self) -> bool:
        """Test: Start first conversation and create persistent session"""
        try:
            payload = {
                "prompt": "Hello! I'm testing the persistent session. Please remember that my name is TestUser and I'm working on a Python project called 'GeminiTest'."
            }
            if self.api_key:
                payload["api_key"] = self.api_key
            
            response = requests.post(
                f"{self.base_url}/environments/{self.env_id}/gemini/session",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('persistent') and 'response' in data:
                    self.log_test("First Conversation", True, f"Response length: {len(data['response'])} chars")
                    return True
                else:
                    self.log_test("First Conversation", False, f"Unexpected response format: {data}")
                    return False
            else:
                self.log_test("First Conversation", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("First Conversation", False, f"Exception: {str(e)}")
            return False
    
    def test_session_status_active(self) -> bool:
        """Test: Check session status when session is active"""
        try:
            response = requests.get(f"{self.base_url}/environments/{self.env_id}/gemini/session/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('active') and data.get('context_managed_by') == 'gemini_cli_internal':
                    self.log_test("Session Status (Active)", True, f"Session active, created at: {data.get('created_at')}")
                    return True
                else:
                    self.log_test("Session Status (Active)", False, f"Session not active: {data}")
                    return False
            else:
                self.log_test("Session Status (Active)", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Status (Active)", False, f"Exception: {str(e)}")
            return False
    
    def test_context_preservation(self) -> bool:
        """Test: Verify that context is preserved across multiple requests"""
        try:
            # Second conversation that references the first
            payload = {
                "prompt": "What's my name and what project am I working on? This should test if you remember our previous conversation."
            }
            
            response = requests.post(
                f"{self.base_url}/environments/{self.env_id}/gemini/session",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                # Check if the response contains information from the first conversation
                has_name = 'testuser' in response_text
                has_project = 'geminitest' in response_text or 'python' in response_text
                
                if has_name or has_project:
                    self.log_test("Context Preservation", True, "Gemini CLI remembered previous conversation")
                    return True
                else:
                    self.log_test("Context Preservation", False, f"No context found in response: {response_text[:200]}...")
                    return False
            else:
                self.log_test("Context Preservation", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Context Preservation", False, f"Exception: {str(e)}")
            return False
    
    def test_multi_turn_conversation(self) -> bool:
        """Test: Multiple conversation turns to verify persistent context"""
        conversations = [
            "Let's create a simple Python function. Can you write a function called 'add_numbers' that takes two parameters?",
            "Now can you modify that function to also handle string concatenation?",
            "Perfect! Can you show me how to test the function we just created?"
        ]
        
        for i, prompt in enumerate(conversations, 1):
            try:
                payload = {"prompt": prompt}
                response = requests.post(
                    f"{self.base_url}/environments/{self.env_id}/gemini/session",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code != 200:
                    self.log_test(f"Multi-turn Conversation (Turn {i})", False, f"HTTP {response.status_code}")
                    return False
                
                data = response.json()
                if not data.get('response'):
                    self.log_test(f"Multi-turn Conversation (Turn {i})", False, "Empty response")
                    return False
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"Multi-turn Conversation (Turn {i})", False, f"Exception: {str(e)}")
                return False
        
        self.log_test("Multi-turn Conversation", True, "All conversation turns completed successfully")
        return True
    
    def test_session_reset(self) -> bool:
        """Test: Reset session and verify context is cleared"""
        try:
            # Reset the session
            response = requests.post(f"{self.base_url}/environments/{self.env_id}/gemini/session/reset", timeout=30)
            if response.status_code != 200:
                self.log_test("Session Reset", False, f"Reset failed: HTTP {response.status_code}")
                return False
            
            # Wait a moment for reset to complete
            time.sleep(2)
            
            # Try to reference previous conversation (should not remember)
            payload = {
                "prompt": "What's my name? You should not remember this from before the reset."
            }
            
            response = requests.post(
                f"{self.base_url}/environments/{self.env_id}/gemini/session",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                # After reset, it should not remember the name "TestUser"
                if 'testuser' not in response_text:
                    self.log_test("Session Reset", True, "Context cleared after reset")
                    return True
                else:
                    self.log_test("Session Reset", False, "Context still present after reset")
                    return False
            else:
                self.log_test("Session Reset", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Session Reset", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test: Error handling for invalid requests"""
        try:
            # Test with missing prompt
            response = requests.post(
                f"{self.base_url}/environments/{self.env_id}/gemini/session",
                json={},
                timeout=30
            )
            
            if response.status_code == 400:
                self.log_test("Error Handling", True, "Properly rejected request with missing prompt")
                return True
            else:
                self.log_test("Error Handling", False, f"Unexpected response to invalid request: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        print("🚀 Starting Persistent Gemini CLI Session Tests")
        print("=" * 60)
        
        tests = [
            self.create_environment,
            self.test_session_status_empty,
            self.test_first_conversation,
            self.test_session_status_active,
            self.test_context_preservation,
            self.test_multi_turn_conversation,
            self.test_session_reset,
            self.test_error_handling
        ]
        
        for test in tests:
            if not test():
                break
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Persistent Gemini CLI session is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
            return False

def main():
    parser = argparse.ArgumentParser(description='Test persistent Gemini CLI session functionality')
    parser.add_argument('--api-key', help='Gemini API key for testing')
    parser.add_argument('--base-url', default='http://localhost:8081', help='Base URL for the service')
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("⚠️  Warning: No API key provided. Tests may fail if API key is not configured in the service.")
        print("   Use --api-key YOUR_API_KEY to provide an API key for testing.")
        print()
    
    tester = GeminiSessionTester(base_url=args.base_url, api_key=args.api_key)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

#!/bin/bash

# Test Persistent Gemini CLI Session with curl commands
# This script tests the session persistence functionality

echo "🧪 Testing Persistent Gemini CLI Session with curl"
echo "=================================================="

BASE_URL="http://localhost:8081"

# Check if API key is provided
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY environment variable not set."
    echo "   You can set it with: export GEMINI_API_KEY=your_api_key"
    echo "   Or the script will try to use the configured API key in the agent."
else
    echo "✅ Using provided GEMINI_API_KEY"
fi

# Step 1: Create Environment
echo -e "\n1. Creating environment..."
ENV_RESPONSE=$(curl -s -X POST "$BASE_URL/environments")
echo "Environment response: $ENV_RESPONSE"

# Extract env_id from response
ENV_ID=$(echo "$ENV_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['env_id'])" 2>/dev/null)

if [ -z "$ENV_ID" ]; then
    echo "❌ Failed to create environment or extract env_id"
    exit 1
fi

echo "✅ Environment created: $ENV_ID"

# Step 2: Check initial session status
echo -e "\n2. Checking initial session status..."
curl -s -X GET "$BASE_URL/environments/$ENV_ID/gemini/session/status" | python3 -m json.tool

# Step 3: First conversation - establish context
echo -e "\n3. First conversation (establishing context)..."
if [ ! -z "$GEMINI_API_KEY" ]; then
  FIRST_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Hello! Please remember that my name is Alice and I am testing session persistence. My favorite color is blue. Please acknowledge this and tell me you will remember it.\",
      \"api_key\": \"$GEMINI_API_KEY\"
    }")
else
  FIRST_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Hello! Please remember that my name is Alice and I am testing session persistence. My favorite color is blue. Please acknowledge this and tell me you will remember it.\"
    }")
fi

echo "First response:"
echo "$FIRST_RESPONSE" | python3 -m json.tool

# Step 4: Check session status after first conversation
echo -e "\n4. Checking session status after first conversation..."
curl -s -X GET "$BASE_URL/environments/$ENV_ID/gemini/session/status" | python3 -m json.tool

# Step 5: Second conversation - test context persistence
echo -e "\n5. Second conversation (testing context persistence)..."
if [ ! -z "$GEMINI_API_KEY" ]; then
  SECOND_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"What is my name and what is my favorite color? This tests if you remember our previous conversation.\",
      \"api_key\": \"$GEMINI_API_KEY\"
    }")
else
  SECOND_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"What is my name and what is my favorite color? This tests if you remember our previous conversation.\"
    }")
fi

echo "Second response:"
echo "$SECOND_RESPONSE" | python3 -m json.tool

# Step 6: Third conversation - more context testing
echo -e "\n6. Third conversation (more context testing)..."
if [ ! -z "$GEMINI_API_KEY" ]; then
  THIRD_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Now I want to add more information: I work as a software engineer and I live in San Francisco. Please remember this additional information.\",
      \"api_key\": \"$GEMINI_API_KEY\"
    }")
else
  THIRD_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Now I want to add more information: I work as a software engineer and I live in San Francisco. Please remember this additional information.\"
    }")
fi

echo "Third response:"
echo "$THIRD_RESPONSE" | python3 -m json.tool

# Step 7: Fourth conversation - comprehensive context test
echo -e "\n7. Fourth conversation (comprehensive context test)..."
if [ ! -z "$GEMINI_API_KEY" ]; then
  FOURTH_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Can you summarize everything you know about me from our conversation? Include my name, favorite color, job, and location.\",
      \"api_key\": \"$GEMINI_API_KEY\"
    }")
else
  FOURTH_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Can you summarize everything you know about me from our conversation? Include my name, favorite color, job, and location.\"
    }")
fi

echo "Fourth response:"
echo "$FOURTH_RESPONSE" | python3 -m json.tool

# Step 8: Check final session status
echo -e "\n8. Checking final session status..."
curl -s -X GET "$BASE_URL/environments/$ENV_ID/gemini/session/status" | python3 -m json.tool

# Step 9: Test session reset
echo -e "\n9. Testing session reset..."
RESET_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session/reset")
echo "Reset response:"
echo "$RESET_RESPONSE" | python3 -m json.tool

# Step 10: Test conversation after reset (should not remember previous context)
echo -e "\n10. Testing conversation after reset..."
if [ ! -z "$GEMINI_API_KEY" ]; then
  AFTER_RESET_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Do you remember my name and favorite color from our previous conversation?\",
      \"api_key\": \"$GEMINI_API_KEY\"
    }")
else
  AFTER_RESET_RESPONSE=$(curl -s -X POST "$BASE_URL/environments/$ENV_ID/gemini/session" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Do you remember my name and favorite color from our previous conversation?\"
    }")
fi

echo "After reset response:"
echo "$AFTER_RESET_RESPONSE" | python3 -m json.tool

echo -e "\n✅ Session persistence test completed!"
echo "Environment ID used: $ENV_ID"

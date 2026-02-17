#!/bin/bash

# Agent Ops Backend - Job Testing Script
# Tests all supported job types using Authorization: Bearer dev-key-12345

BASE_URL="http://localhost:8080"
API_KEY="dev-key-12345"
HEADERS="Content-Type: application/json"
AUTH="Authorization: Bearer $API_KEY"

echo "🧪 Agent Ops Backend - Job Testing Script"
echo "========================================="
echo "Base URL: $BASE_URL"
echo "API Key: $API_KEY"
echo ""

# Test health endpoint
echo "1️⃣  Testing health endpoint..."
curl -s "$BASE_URL/health" | jq '.' || echo "❌ Health check failed"
echo ""

# Test prompt_pack job
echo "2️⃣  Creating prompt_pack job..."
PROMPT_PACK_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
  -H "$HEADERS" \
  -H "$AUTH" \
  -d '{
    "type": "prompt_pack",
    "params": {
      "feature_name": "User Dashboard Analytics",
      "feature_description": "Add real-time analytics dashboard showing user engagement metrics, conversion funnels, and performance indicators",
      "notes": "Must integrate with existing React frontend and Node.js backend. Consider mobile responsiveness."
    }
  }')

PROMPT_PACK_ID=$(echo "$PROMPT_PACK_RESPONSE" | jq -r '.id')
echo "Created prompt_pack job: $PROMPT_PACK_ID"
echo ""

# Test research_brief job
echo "3️⃣  Creating research_brief job..."
RESEARCH_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
  -H "$HEADERS" \
  -H "$AUTH" \
  -d '{
    "type": "research_brief",
    "params": {
      "topic": "API Performance Optimization",
      "questions": ["What are the slowest endpoints in our API?", "What causes database query timeouts?", "How can we improve response times?"],
      "context_notes": "P95 response times increased 200% this month. Database queries taking 5+ seconds. Users reporting slow page loads."
    }
  }')

RESEARCH_ID=$(echo "$RESEARCH_RESPONSE" | jq -r '.id')
echo "Created research_brief job: $RESEARCH_ID"
echo ""

# Test weekly_pilot_memo job  
echo "4️⃣  Creating weekly_pilot_memo job..."
MEMO_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
  -H "$HEADERS" \
  -H "$AUTH" \
  -d '{
    "type": "weekly_pilot_memo",
    "params": {
      "pilot_name": "E-commerce Checkout Optimization",
      "week_start_date": "2026-02-10",
      "notes": "Implemented new payment flow on Tuesday. Added guest checkout option. Fixed mobile layout issues on Thursday."
    }
  }')

MEMO_ID=$(echo "$MEMO_RESPONSE" | jq -r '.id')
echo "Created weekly_pilot_memo job: $MEMO_ID"
echo ""

# Test deprecated lead_list (should return deprecation notice)
echo "5️⃣  Testing deprecated lead_list job..."
LEAD_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
  -H "$HEADERS" \
  -H "$AUTH" \
  -d '{
    "type": "lead_list",
    "params": {
      "city": "San Francisco",
      "industry": "tech"
    }
  }')

LEAD_ID=$(echo "$LEAD_RESPONSE" | jq -r '.id')
echo "Created lead_list job (deprecated): $LEAD_ID"
echo ""

# Wait for jobs to complete
echo "⏳ Waiting for jobs to complete..."
sleep 10
echo ""

# Check all jobs status
echo "6️⃣  Checking all jobs status..."
curl -s "$BASE_URL/jobs" -H "$AUTH" | jq '.[] | {id, type, status}' || echo "❌ Jobs list failed"
echo ""

# Get outputs for each job type
if [ "$PROMPT_PACK_ID" != "null" ]; then
    echo "7️⃣  Getting prompt_pack output..."
    curl -s "$BASE_URL/outputs/latest?type=prompt_pack" -H "$AUTH" | jq '.content_text[:200]' || echo "❌ No prompt_pack output yet"
    echo ""
fi

if [ "$RESEARCH_ID" != "null" ]; then
    echo "8️⃣  Getting research_brief output..."
    curl -s "$BASE_URL/outputs/latest?type=research_brief" -H "$AUTH" | jq '.content_text[:200]' || echo "❌ No research_brief output yet"
    echo ""
fi

if [ "$MEMO_ID" != "null" ]; then
    echo "9️⃣  Getting weekly_pilot_memo output..."
    curl -s "$BASE_URL/outputs/latest?type=weekly_pilot_memo" -H "$AUTH" | jq '.content_text[:200]' || echo "❌ No weekly_pilot_memo output yet"
    echo ""
fi

if [ "$LEAD_ID" != "null" ]; then
    echo "🔟 Getting lead_list output (deprecated)..."
    curl -s "$BASE_URL/outputs/latest?type=lead_list" -H "$AUTH" | jq '.content_text[:200]' || echo "❌ No lead_list output yet"
    echo ""
fi

echo "✅ Test script completed!"
echo ""
echo "📝 Job IDs created:"
echo "   prompt_pack: $PROMPT_PACK_ID"
echo "   research_brief: $RESEARCH_ID" 
echo "   weekly_pilot_memo: $MEMO_ID"
echo "   lead_list (deprecated): $LEAD_ID"
echo ""
echo "💡 To get full outputs, use:"
echo "   curl -H \"Authorization: Bearer dev-key-12345\" \"$BASE_URL/jobs/{job_id}/output\""
#!/bin/bash
# Test NLP API endpoints

echo "Testing NLP API..."
echo ""

# First, login to get a token
echo "1. Getting authentication token..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecureAdmin123!"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token. Is the server running?"
  echo "Start server with: source venv/bin/activate && python src/dashboard/server.py"
  exit 1
fi

echo "✓ Got token: ${TOKEN:0:20}..."
echo ""

# Test NLP status
echo "2. Testing NLP status endpoint..."
curl -s http://localhost:5000/api/nlp/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Test alert analysis
echo "3. Testing alert analysis..."
curl -s -X POST http://localhost:5000/api/nlp/analyze-alert \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Critical SYN flood attack detected from 192.168.1.100","attack_type":"syn_flood"}' | python3 -m json.tool
echo ""

# Test IP enrichment
echo "4. Testing IP enrichment..."
curl -s -X POST http://localhost:5000/api/nlp/enrich-ip \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip":"192.168.1.100"}' | python3 -m json.tool
echo ""

echo "✓ NLP API test complete!"

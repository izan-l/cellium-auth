#!/bin/bash

# Quick verification script for Cellium MCP setup
echo "🔧 Cellium MCP Quick Verification"
echo "================================="

# Check if services are running
echo "✅ Auth Service (port 8000):"
curl -s http://localhost:8000/health 2>/dev/null | grep -q "healthy" && echo "  ✓ Running and healthy" || echo "  ✗ Not running or unhealthy"

echo ""
echo "✅ Processor Service (port 3000):"
curl -s --connect-timeout 2 http://localhost:3000/ >/dev/null 2>&1 && echo "  ✓ Responding" || echo "  ✗ Not responding"

echo ""
echo "🔑 Token Generation:"
TOKEN=$(curl -s http://localhost:8000/auth/test-token 2>/dev/null | grep -o '"token":"[^"]*' | cut -d'"' -f4)
if [ ! -z "$TOKEN" ]; then
    echo "  ✓ Generated token: ${TOKEN:0:20}..."
    echo ""
    echo "🔍 Token Validation:"
    curl -s -X POST http://localhost:8000/auth/validate -H "Content-Type: application/json" -d "{\"token\":\"$TOKEN\"}" 2>/dev/null | grep -q '"valid":true' && echo "  ✓ Token validates successfully" || echo "  ✗ Token validation failed"
    
    echo ""
    echo "📋 Codex Configuration Update:"
    echo "  Add this to your ~/.codex/config.toml:"
    echo ""
    echo "  [mcp_servers.cellium-local]"
    echo "  url = \"http://localhost:3000/sse\""
    echo "  token = \"$TOKEN\""
    echo "  enabled = true"
else
    echo "  ✗ Failed to generate token"
fi

echo ""
echo "🎯 Next Steps:"
echo "  1. Update your Codex config with the token above"
echo "  2. Restart Codex"
echo "  3. Test MCP connection in your AI client"
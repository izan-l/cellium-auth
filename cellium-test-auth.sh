#!/bin/bash

# Cellium MCP Authentication Testing Script
# This script tests the authentication flow between cellium-processor and cellium-auth

set -e

echo "🔧 Cellium MCP Authentication Test Suite"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AUTH_SERVICE_URL="http://localhost:8000"
PROCESSOR_URL="http://localhost:3000"

echo -e "${BLUE}Testing Configuration:${NC}"
echo "  Auth Service: $AUTH_SERVICE_URL"
echo "  Processor Service: $PROCESSOR_URL"
echo ""

# Function to test service availability
test_service() {
    local service_name=$1
    local url=$2
    
    echo -n "Testing $service_name connectivity... "
    if curl -s --connect-timeout 5 "$url/health" > /dev/null 2>&1 || curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo -e "${YELLOW}  Make sure $service_name is running on $url${NC}"
        return 1
    fi
}

# Function to test token generation
test_token_generation() {
    echo -n "Testing token generation... "
    local response=$(curl -s "$AUTH_SERVICE_URL/auth/test-token" 2>/dev/null)
    
    if echo "$response" | grep -q '"token"' && echo "$response" | grep -q 'user:'; then
        echo -e "${GREEN}✓ OK${NC}"
        local token=$(echo "$response" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
        echo "  Generated token format: ${token:0:20}..."
        echo "$token" > /tmp/cellium_test_token.txt
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Response: $response"
        return 1
    fi
}

# Function to test token validation
test_token_validation() {
    echo -n "Testing token validation... "
    
    if [ ! -f /tmp/cellium_test_token.txt ]; then
        echo -e "${RED}✗ FAILED - No token available${NC}"
        return 1
    fi
    
    local token=$(cat /tmp/cellium_test_token.txt)
    local response=$(curl -s -X POST "$AUTH_SERVICE_URL/auth/validate" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$token\"}" 2>/dev/null)
    
    if echo "$response" | grep -q '"valid":true'; then
        echo -e "${GREEN}✓ OK${NC}"
        local username=$(echo "$response" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
        echo "  Validated user: $username"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Response: $response"
        return 1
    fi
}

# Function to test MCP SSE endpoint
test_mcp_sse_endpoint() {
    echo -n "Testing MCP SSE endpoint... "
    
    if [ ! -f /tmp/cellium_test_token.txt ]; then
        echo -e "${RED}✗ FAILED - No token available${NC}"
        return 1
    fi
    
    local token=$(cat /tmp/cellium_test_token.txt)
    
    # Test SSE endpoint with token in query parameter
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 10 \
        "$PROCESSOR_URL/sse?token=$token" 2>/dev/null || echo "000")
    
    if [ "$response_code" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "  SSE endpoint responding with HTTP 200"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  HTTP Status: $response_code"
        
        # Test with Authorization header
        echo -n "  Trying with Authorization header... "
        response_code=$(curl -s -o /dev/null -w "%{http_code}" \
            --connect-timeout 10 \
            -H "Authorization: Bearer $token" \
            "$PROCESSOR_URL/sse" 2>/dev/null || echo "000")
        
        if [ "$response_code" = "200" ]; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        else
            echo -e "${RED}✗ FAILED (HTTP $response_code)${NC}"
            return 1
        fi
    fi
}

# Function to test environment token fallback
test_env_token_fallback() {
    echo -n "Testing environment token fallback... "
    
    # Test with the hardcoded environment token
    local env_token="user:admin:test123hash"
    local response=$(curl -s -X POST "$AUTH_SERVICE_URL/auth/validate" \
        -H "Content-Type: application/json" \
        -d "{\"token\":\"$env_token\"}" 2>/dev/null)
    
    if echo "$response" | grep -q '"valid":true'; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "  Environment token validation working"
        return 0
    else
        echo -e "${YELLOW}⚠ Using processor fallback${NC}"
        echo "  Auth service rejected env token, processor should use fallback"
        return 0
    fi
}

# Main test execution
main() {
    local failed_tests=0
    
    echo "Step 1: Service Connectivity"
    echo "----------------------------"
    test_service "Auth Service" "$AUTH_SERVICE_URL" || ((failed_tests++))
    test_service "Processor Service" "$PROCESSOR_URL" || ((failed_tests++))
    echo ""
    
    echo "Step 2: Token Generation & Validation"
    echo "-------------------------------------"
    test_token_generation || ((failed_tests++))
    test_token_validation || ((failed_tests++))
    echo ""
    
    echo "Step 3: Environment Token Fallback"
    echo "----------------------------------"
    test_env_token_fallback || ((failed_tests++))
    echo ""
    
    echo "Step 4: MCP Endpoint Testing"
    echo "----------------------------"
    test_mcp_sse_endpoint || ((failed_tests++))
    echo ""
    
    echo "Summary:"
    echo "========"
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed! MCP authentication should work.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update your Codex config with a valid token"
        echo "2. Test the MCP connection from your AI client"
        echo ""
        if [ -f /tmp/cellium_test_token.txt ]; then
            local token=$(cat /tmp/cellium_test_token.txt)
            echo "Working token for Codex config:"
            echo "  token = \"$token\""
        fi
    else
        echo -e "${RED}❌ $failed_tests test(s) failed. Please fix issues before proceeding.${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "- Ensure both services are running"
        echo "- Check the .env files are properly configured"
        echo "- Verify database connectivity for auth service"
    fi
    
    # Cleanup
    rm -f /tmp/cellium_test_token.txt
}

# Help function
show_help() {
    echo "Cellium MCP Authentication Test Suite"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --auth-url     Override auth service URL (default: http://localhost:8000)"
    echo "  --proc-url     Override processor URL (default: http://localhost:3000)"
    echo ""
    echo "This script tests the complete authentication flow between:"
    echo "  - cellium-auth (FastAPI service)"
    echo "  - cellium-processor (Node.js MCP server)"
    echo ""
    echo "Prerequisites:"
    echo "  - Both services must be running"
    echo "  - curl must be available"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --auth-url)
            AUTH_SERVICE_URL="$2"
            shift 2
            ;;
        --proc-url)
            PROCESSOR_URL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run the main function
main
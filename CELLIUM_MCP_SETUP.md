# Cellium MCP Authentication Setup & Troubleshooting Guide

## Overview

This guide helps you fix the MCP handshake issues between cellium-processor and cellium-auth services. The authentication flow works as follows:

1. **Token Generation**: cellium-auth generates tokens in format `user:username:randomhash`
2. **Token Validation**: cellium-processor validates tokens via `/auth/validate` endpoint
3. **MCP Connection**: Authenticated clients connect via `/sse` endpoint with SSE transport
4. **Fallback Support**: Legacy environment token fallback for development

## Quick Setup

### 1. Start cellium-auth Service

```bash
cd /Users/izan_l/Projects/cellium-auth
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at: http://localhost:8000

### 2. Start cellium-processor Service

```bash
cd /Users/izan_l/Projects/cellium-processor/apps/cellium-processor
npm install  # if needed
npm run dev
```

The service will be available at: http://localhost:3000

### 3. Run Authentication Tests

```bash
cd /Users/izan_l/Projects
./cellium-test-auth.sh
```

This will test the complete authentication flow and provide detailed feedback.

## Configuration Details

### cellium-processor Configuration (.env)

Key settings in `/Users/izan_l/Projects/cellium-processor/apps/cellium-processor/.env`:

```bash
# Use local auth service instead of remote
AUTH_SERVICE_URL=http://localhost:8000

# Enable debug logging
LOG_LEVEL=debug

# Enable fallback for testing
ALLOW_LEGACY_ENV_TOKEN_FALLBACK=true

# Test tokens (for fallback testing)
TOKEN_admin=user:admin:test123hash
TOKEN_testuser=user:testuser:dev456hash
```

### cellium-auth Configuration (.env)

Current settings in `/Users/izan_l/Projects/cellium-auth/.env`:

```bash
DATABASE_URL=sqlite:///./test.db
JWT_SECRET_KEY=dev-secret-key-change-in-production
HOST=0.0.0.0
PORT=8000
DEBUG=true
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

### Codex Configuration (~/.codex/config.toml)

Updated MCP server configuration:

```toml
[mcp_servers.cellium-local]
url = "http://localhost:3000/sse"
token = "user:admin:test123hash"  # Use working token from test
enabled = true
startup_timeout_sec = 60
```

## Troubleshooting Steps

### Issue 1: "Auth service validation failed"

**Symptoms:**
- MCP connection fails with authentication errors
- Logs show "Auth service validation failed"

**Solutions:**
1. Verify auth service is running: `curl http://localhost:8000/health`
2. Check AUTH_SERVICE_URL in processor .env file
3. Test token validation: `curl -X POST http://localhost:8000/auth/validate -H "Content-Type: application/json" -d '{"token":"user:admin:test123hash"}'`

### Issue 2: "Token validation unavailable"

**Symptoms:**
- MCP server rejects all tokens
- No fallback to environment variables

**Solutions:**
1. Set `ALLOW_LEGACY_ENV_TOKEN_FALLBACK=true` in processor .env
2. Add test tokens with `TOKEN_` prefix in processor .env
3. Restart processor service to load new environment

### Issue 3: "No active MCP connection for user"

**Symptoms:**
- SSE connection established but `/messages` endpoint fails
- Logs show transport not found for user

**Solutions:**
1. Ensure SSE connection is established first: `curl "http://localhost:3000/sse?token=user:admin:test123hash"`
2. Check token consistency between SSE and messages endpoints
3. Verify user mapping in logs

### Issue 4: Token Format Issues

**Symptoms:**
- Tokens generated in wrong format
- Validation fails with format errors

**Solutions:**
1. Verify token generation in auth service: `curl http://localhost:8000/auth/test-token`
2. Check Token model in `/Users/izan_l/Projects/cellium-auth/app/models/models.py`
3. Expected format: `user:username:randomhash`

## Testing Authentication Flow

### Manual Testing Steps

1. **Generate a test token:**
```bash
curl http://localhost:8000/auth/test-token
```

2. **Validate the token:**
```bash
curl -X POST http://localhost:8000/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN_HERE"}'
```

3. **Test SSE endpoint:**
```bash
curl "http://localhost:3000/sse?token=YOUR_TOKEN_HERE"
```

4. **Test with Codex:**
   - Update token in `~/.codex/config.toml`
   - Restart Codex
   - Try connecting to the MCP server

### Automated Testing

Run the comprehensive test suite:

```bash
cd /Users/izan_l/Projects
./cellium-test-auth.sh
```

This tests:
- Service connectivity
- Token generation & validation
- Environment token fallback
- MCP SSE endpoint authentication

## Development Workflow

1. **Make changes** to auth configuration
2. **Restart services** (auth and processor)
3. **Run tests** with `./cellium-test-auth.sh`
4. **Update Codex config** with working token
5. **Test MCP connection** in your AI client

## Debug Logging

Enable detailed logging in both services:

**cellium-processor:**
- Set `LOG_LEVEL=debug` in .env
- Check logs for auth validation attempts

**cellium-auth:**
- Set `DEBUG=true` in .env
- Check FastAPI logs for validation requests

## Common Token Examples

Working tokens for testing:

```bash
# Environment fallback tokens (in processor .env)
TOKEN_admin=user:admin:test123hash
TOKEN_testuser=user:testuser:dev456hash

# Generated tokens (from auth service)
user:admin:a1b2c3d4e5f6  # 12-char random suffix
user:testuser:f6e5d4c3b2a1
```

## Port Configuration

| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| cellium-auth | 8000 | `/auth/validate` | Token validation |
| cellium-processor | 3000 | `/sse` | MCP SSE transport |
| cellium-processor | 3000 | `/messages` | MCP message handling |

## Success Indicators

✅ **Authentication working correctly when:**
- Test script passes all tests
- SSE endpoint returns HTTP 200
- Token validation returns `{"valid": true, "user": {...}}`
- MCP client can connect and execute tools
- Logs show successful authentication flows

## Next Steps After Setup

1. **Verify end-to-end flow** with your AI client
2. **Create production tokens** for real usage
3. **Update security configuration** for production deployment
4. **Monitor authentication logs** for issues

For additional help, check the logs in both services and run the test script for detailed diagnostics.
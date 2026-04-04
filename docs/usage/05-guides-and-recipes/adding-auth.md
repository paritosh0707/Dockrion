# 5.3 Adding Auth

[Home](../../README.md) > [Guides & Recipes](README.md)

Step-by-step guide to adding authentication to an existing agent.

## Option 1: CLI Quick-Add

The fastest way:

```bash
# Add API key auth (default)
dockrion add auth

# Add JWT auth
dockrion add auth --mode jwt

# Custom env var and header
dockrion add auth --env-var MY_API_KEY --header X-Custom-Auth

# Remove auth
dockrion add auth --mode none
```

This modifies your `Dockfile.yaml` in place, adding or updating the `auth` section.

## Option 2: Manual Configuration

### API Key Auth

1. Add the `auth` section to your Dockfile:

```yaml
auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY
    header: X-API-Key
    allow_bearer: true
```

2. Set the environment variable:

```bash
echo "DOCKRION_API_KEY=my-secret-key-123" >> .env
```

3. Declare the secret:

```yaml
secrets:
  required:
    - name: DOCKRION_API_KEY
      description: "API key for authenticating callers"
```

4. Test:

```bash
dockrion run

# Without key → 401
curl http://localhost:8080/invoke -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# With key → 200
curl http://localhost:8080/invoke -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-secret-key-123" \
  -d '{"query": "test"}'
```

### JWT Auth

1. Install the JWT extra:

```bash
pip install dockrion[jwt]
```

2. Configure in Dockfile:

```yaml
auth:
  mode: jwt
  jwt:
    jwks_url: https://your-idp.com/.well-known/jwks.json
    issuer: https://your-idp.com/
    audience: my-agent-api
    algorithms: [RS256]
```

3. Test with a JWT token from your identity provider:

```bash
TOKEN="eyJhbGciOiJSUzI1NiIs..."
curl http://localhost:8080/invoke -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "test"}'
```

## Adding Roles

After auth is configured, add roles for fine-grained access:

```yaml
auth:
  mode: api_key
  api_keys:
    env_var: DOCKRION_API_KEY
  roles:
    - name: admin
      permissions: [deploy, invoke, view_metrics, key_manage]
    - name: user
      permissions: [invoke, read_docs]
  rate_limits:
    admin: "5000/hour"
    user: "100/hour"
```

## Verifying in Swagger

After adding auth, open `http://localhost:8080/docs`. You should see an **Authorize** button. Click it to enter your API key or JWT, then use "Try it out" on protected endpoints.

---

**Previous:** [5.2 Environment & Secrets](environment-and-secrets.md) | **Next:** [5.4 Adding Streaming →](adding-streaming.md)

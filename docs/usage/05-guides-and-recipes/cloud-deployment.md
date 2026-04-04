# 5.7 Cloud Deployment

[Home](../../README.md) > [Guides & Recipes](README.md)

Reference patterns for deploying Dockrion images to major cloud platforms.

> **Note:** `dockrion deploy` is **not yet implemented**. For now, build locally with `dockrion build` and deploy the Docker image using your cloud provider's tools.

## What the Image Needs at Runtime

| Requirement | How to provide |
|-------------|----------------|
| Environment variables (secrets) | Cloud provider's secrets management |
| Port 8080 exposed | Container port mapping |
| Health check endpoint | `GET /health` returns 200 when running |
| Readiness probe | `GET /ready` returns 200 when agent is loaded |

## AWS ECS / Fargate

```json
{
  "containerDefinitions": [
    {
      "name": "agent",
      "image": "your-ecr-repo/dockrion/my-agent:v1.0.0",
      "portMappings": [
        { "containerPort": 8080, "protocol": "tcp" }
      ],
      "environment": [
        { "name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..." }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Steps

1. Push image to ECR: `docker tag dockrion/my-agent:v1.0.0 <ecr-url>:v1.0.0 && docker push <ecr-url>:v1.0.0`
2. Create task definition with the container config above
3. Configure secrets via AWS Secrets Manager
4. Create a service with an ALB target group pointing to port 8080

## Google Cloud Run

```bash
# Push to Artifact Registry
docker tag dockrion/my-agent:v1.0.0 \
  us-central1-docker.pkg.dev/PROJECT/repo/my-agent:v1.0.0
docker push us-central1-docker.pkg.dev/PROJECT/repo/my-agent:v1.0.0

# Deploy
gcloud run deploy my-agent \
  --image us-central1-docker.pkg.dev/PROJECT/repo/my-agent:v1.0.0 \
  --port 8080 \
  --set-env-vars OPENAI_API_KEY=sk-... \
  --allow-unauthenticated \
  --region us-central1
```

Cloud Run automatically uses the container's port and health check. For secrets, use `--set-secrets` with Secret Manager:

```bash
gcloud run deploy my-agent \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

## Azure Container Apps

```bash
# Push to ACR
az acr login --name myregistry
docker tag dockrion/my-agent:v1.0.0 myregistry.azurecr.io/my-agent:v1.0.0
docker push myregistry.azurecr.io/my-agent:v1.0.0

# Create container app
az containerapp create \
  --name my-agent \
  --resource-group mygroup \
  --environment myenv \
  --image myregistry.azurecr.io/my-agent:v1.0.0 \
  --target-port 8080 \
  --ingress external \
  --env-vars OPENAI_API_KEY=secretref:openai-key
```

## Health Check Configuration

All cloud platforms support health checks. Point them at:

| Probe | Endpoint | Expected |
|-------|----------|----------|
| **Liveness** | `GET /health` | 200 (always, if process is alive) |
| **Readiness** | `GET /ready` | 200 only when agent adapter is loaded |
| **Startup** | `GET /ready` | 200 (with longer initial delay for agent loading) |

Recommended settings:

- Initial delay: 10–30 seconds (agent loading time)
- Interval: 30 seconds
- Timeout: 5 seconds
- Failure threshold: 3

---

**Previous:** [5.6 Docker Build](docker-build-and-deployment.md) | **Next:** [5.8 Troubleshooting →](troubleshooting.md)

# Deployment Guide

This guide covers deploying Bloginator in various environments, from local Docker to cloud platforms.

---

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Docker Compose](#docker-compose)
3. [Cloud Deployment](#cloud-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Docker Deployment

### Building the Image

```bash
# Build the Docker image
docker build -t bloginator:latest .

# Build with specific version tag
docker build -t bloginator:1.0.0 .
```

### Running the Container

```bash
# Run with default settings (web UI on port 8000)
docker run -p 8000:8000 -v $(pwd)/data:/data bloginator:latest

# Run with custom LLM configuration
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e BLOGINATOR_LLM_PROVIDER=custom \
  -e BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1 \
  -e BLOGINATOR_LLM_API_KEY=your-api-key \
  bloginator:latest

# Run CLI commands
docker run -v $(pwd)/data:/data bloginator:latest \
  bloginator extract /data/corpus -o /data/extracted
```

### Volume Mounts

Mount these directories for persistence:

- `/data`: Application data (indices, generated content)
- `/corpus`: Your source documents (read-only)
- `/root/.cache`: Embedding model cache (optional, speeds up startup)

---

## Docker Compose

### Quick Start

```bash
# Start all services (Bloginator + Ollama)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Configuration

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # LLM Provider (ollama, custom, mock)
  - BLOGINATOR_LLM_PROVIDER=ollama
  - BLOGINATOR_LLM_MODEL=llama3

  # For OpenAI-compatible APIs
  - BLOGINATOR_LLM_PROVIDER=custom
  - BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1
  - BLOGINATOR_LLM_API_KEY=your-api-key

  # Logging
  - BLOGINATOR_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Using Different LLM Models

```bash
# Use different Ollama model
docker-compose exec ollama ollama pull mistral
# Update BLOGINATOR_LLM_MODEL in docker-compose.yml to "mistral"
docker-compose restart bloginator
```

---

## Cloud Deployment

### AWS ECS

1. **Build and push image to ECR**:
```bash
aws ecr create-repository --repository-name bloginator
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag bloginator:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/bloginator:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/bloginator:latest
```

2. **Create ECS task definition** with:
   - Container: bloginator image from ECR
   - Port mapping: 8000
   - Environment variables for LLM configuration
   - EFS volume for /data persistence

3. **Create ECS service** with:
   - Load balancer for HTTPS
   - Auto-scaling based on CPU/memory
   - Health checks on /health endpoint

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/bloginator

# Deploy to Cloud Run
gcloud run deploy bloginator \
  --image gcr.io/PROJECT_ID/bloginator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --set-env-vars BLOGINATOR_LLM_PROVIDER=custom,BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1 \
  --set-secrets BLOGINATOR_LLM_API_KEY=openai-api-key:latest
```

### Azure Container Instances

```bash
# Create resource group
az group create --name bloginator-rg --location eastus

# Create container instance
az container create \
  --resource-group bloginator-rg \
  --name bloginator \
  --image bloginator:latest \
  --dns-name-label bloginator-app \
  --ports 8000 \
  --environment-variables \
    BLOGINATOR_LLM_PROVIDER=custom \
    BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1 \
  --secure-environment-variables \
    BLOGINATOR_LLM_API_KEY=your-api-key
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOGINATOR_LLM_PROVIDER` | LLM provider (ollama, custom, mock) | `ollama` |
| `BLOGINATOR_LLM_MODEL` | Model name | `llama3` |
| `BLOGINATOR_LLM_BASE_URL` | API base URL | `http://localhost:11434` |
| `BLOGINATOR_LLM_API_KEY` | API key (for custom provider) | - |
| `BLOGINATOR_DATA_DIR` | Data directory path | `/data` |
| `BLOGINATOR_LOG_LEVEL` | Logging level | `INFO` |
| `BLOGINATOR_LLM_MOCK` | Use mock LLM (testing) | `false` |

### Secrets Management

**Never commit API keys to version control!**

Use secrets management:
- **Docker**: Use Docker secrets or environment files
- **Kubernetes**: Use Kubernetes secrets
- **AWS**: Use AWS Secrets Manager
- **GCP**: Use Secret Manager
- **Azure**: Use Key Vault

Example with Docker secrets:
```bash
echo "your-api-key" | docker secret create bloginator_api_key -
docker service create \
  --name bloginator \
  --secret bloginator_api_key \
  --env BLOGINATOR_LLM_API_KEY_FILE=/run/secrets/bloginator_api_key \
  bloginator:latest
```

---

## Monitoring

### Health Checks

The application exposes a health endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Logging

Logs are written to stdout/stderr in JSON format:

```bash
# View logs
docker logs bloginator

# Follow logs
docker logs -f bloginator

# Filter by level
docker logs bloginator 2>&1 | grep ERROR
```

### Metrics

Monitor these metrics:

- **Request latency**: Time to generate outlines/drafts
- **Error rate**: Failed generations
- **Resource usage**: CPU, memory, disk
- **LLM API calls**: Rate and cost

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs bloginator

# Common issues:
# 1. Port already in use
docker ps | grep 8000

# 2. Volume permissions
ls -la data/

# 3. Missing environment variables
docker inspect bloginator | grep -A 20 Env
```

### Slow Performance

1. **Check embedding model cache**:
```bash
docker exec bloginator ls -lh /root/.cache/huggingface
```

2. **Increase container resources**:
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

3. **Use faster LLM**:
   - Switch to smaller model (e.g., llama3:8b instead of llama3:70b)
   - Use cloud API (OpenAI, Anthropic) instead of local Ollama

### Out of Memory

```bash
# Increase memory limit
docker run -m 4g bloginator:latest

# Or in docker-compose.yml
mem_limit: 4g
```

---

## Security Considerations

1. **API Keys**: Use secrets management, never commit to git
2. **Network**: Use HTTPS in production, restrict ports
3. **Updates**: Keep base image and dependencies updated
4. **Scanning**: Scan images for vulnerabilities
5. **Access**: Use authentication for web UI in production

---

## Next Steps

- Set up monitoring and alerting
- Configure backups for /data volume
- Implement CI/CD pipeline
- Add authentication to web UI
- Scale horizontally with load balancer

For questions, see the [User Guide](USER_GUIDE.md) or open an issue on GitHub.

# InstaForLazyPeople - Microservices Monorepo

A Docker containerized monorepo with microservices architecture for automated content processing.

## Architecture

This monorepo orchestrates multiple self-contained services that work together to fetch, polish, and process content:

```
instaforlazypeople/
├── docker-compose.yml          # Orchestrates all services
├── fetcher/                    # Content fetching service
│   ├── Dockerfile
│   ├── models.py
│   ├── main.py
│   └── requirements.txt
├── polisher/                   # Content polishing service
│   ├── Dockerfile
│   ├── models.py
│   ├── main.py
│   └── requirements.txt
└── processor/                  # Content processing service
    ├── Dockerfile
    ├── models.py
    ├── main.py
    └── requirements.txt
```

## Services

### 1. Fetcher Service (Port 8002)
Fetches content from various sources (Instagram, URLs, APIs).

**Endpoints:**
- `GET /health` - Health check
- `POST /fetch` - Fetch content from a source
- `GET /content/{content_id}` - Get fetched content

### 2. Polisher Service (Port 8001)
Enhances and polishes content for better quality.

**Endpoints:**
- `GET /health` - Health check
- `POST /polish` - Polish content
- `GET /result/{content_id}` - Get polish result

### 3. Processor Service (Port 8003)
Processes content with various transformations (resize, filter, compress, etc.).

**Endpoints:**
- `GET /health` - Health check
- `POST /process` - Process content
- `POST /pipeline` - Execute processing pipeline
- `GET /result/{content_id}` - Get process result

### 4. Redis (Port 6379)
Message broker and cache for inter-service communication.

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Running the Services

1. **Start all services:**
```bash
docker-compose up --build
```

2. **Start services in detached mode:**
```bash
docker-compose up -d --build
```

3. **View logs:**
```bash
docker-compose logs -f
```

4. **Stop all services:**
```bash
docker-compose down
```

### Health Checks

Check if services are running:
```bash
# Fetcher
curl http://localhost:8002/health

# Polisher
curl http://localhost:8001/health

# Processor
curl http://localhost:8003/health
```

## Usage Examples

### 1. Fetch Content
```bash
curl -X POST "http://localhost:8002/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "instagram",
    "source_url": "https://instagram.com/example",
    "config": {
      "max_items": 5
    }
  }'
```

### 2. Polish Content
```bash
curl -X POST "http://localhost:8001/polish" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "123",
    "content_type": "image",
    "content_url": "https://example.com/image.jpg",
    "config": {
      "enhance_quality": true,
      "apply_filters": true
    }
  }'
```

### 3. Process Content
```bash
curl -X POST "http://localhost:8003/process" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "123",
    "process_type": "resize",
    "input_url": "https://example.com/image.jpg",
    "parameters": {
      "width": 1080,
      "height": 1080
    }
  }'
```

### 4. Process Pipeline
```bash
curl -X POST "http://localhost:8003/pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "input_url": "https://example.com/image.jpg",
    "stages": ["resize", "filter", "compress"]
  }'
```

## Service Communication

Services communicate via Redis pub/sub channels:
- `fetched_content` - Fetcher publishes to this channel
- `polished_content` - Polisher publishes to this channel
- `processed_content` - Processor publishes to this channel

## Development

### Adding a New Service

1. Create a new directory for your service
2. Add `Dockerfile`, `models.py`, `main.py`, and `requirements.txt`
3. Update `docker-compose.yml` to include the new service
4. Follow the existing service patterns for consistency

### Environment Variables

Each service uses these environment variables:
- `SERVICE_NAME` - Name of the service
- `REDIS_HOST` - Redis hostname (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)

## API Documentation

Once services are running, access interactive API docs:
- Fetcher: http://localhost:8002/docs
- Polisher: http://localhost:8001/docs
- Processor: http://localhost:8003/docs

## Network

All services run on the `microservices-network` bridge network, allowing them to communicate with each other.

## Volumes

Services use volume mounts for hot-reloading during development:
- `./fetcher:/app`
- `./polisher:/app`
- `./processor:/app`

## License

MIT

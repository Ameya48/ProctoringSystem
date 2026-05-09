# Production Deployment Guide

## Overview

This guide covers the complete deployment of the Online Proctoring System for production environments with high availability, scalability, and security.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Frontend      │    │    Backend      │
│  (Load Balancer) │────│   (React App)   │────│   (FastAPI)     │
│   Port: 80/443  │    │   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │    │   MongoDB       │
                       │   Port: 6379    │    │   Port: 27017   │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   RabbitMQ      │    │   Celery        │
                       │   Port: 5672    │    │   Workers       │
                       └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements

- **CPU**: Minimum 4 cores, recommended 8+ cores
- **Memory**: Minimum 8GB RAM, recommended 16GB+ RAM
- **Storage**: Minimum 100GB SSD, recommended 500GB+ SSD
- **Network**: 1Gbps recommended for video streaming
- **OS**: Ubuntu 20.04+ or CentOS 8+

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for HTTPS)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd ProctoringSystem2
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check health endpoints
curl http://localhost/health
curl http://localhost/api/health/detailed
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database Configuration
MONGODB_URI=mongodb://admin:password123@mongodb:27017/proctoring?authSource=admin
REDIS_URL=redis://:redis123@redis:6379/0
RABBITMQ_URL=amqp://admin:rabbit123@rabbitmq:5672/

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
CORS_ORIGINS=https://yourdomain.com

# Performance
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100
AI_MAX_PROCESSING_FPS=10

# Storage (optional)
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=proctoring-storage
```

### SSL Configuration

For production HTTPS:

1. **Obtain SSL certificates** (Let's Encrypt recommended):
```bash
sudo certbot --nginx -d yourdomain.com
```

2. **Update nginx configuration**:
```bash
# Edit nginx/nginx.conf
# Uncomment HTTPS server block
# Update SSL certificate paths
```

3. **Restart services**:
```bash
docker-compose restart nginx
```

## Services

### Backend API

- **Port**: 8000
- **Health Check**: `/health`
- **Metrics**: `/metrics`
- **Workers**: 4 (configurable)

### Frontend

- **Port**: 3000
- **Health Check**: `/health`
- **Static Assets**: Cached for 1 year

### Database Services

#### MongoDB
- **Port**: 27017
- **Persistence**: Docker volume
- **Backup**: Configure automated backups

#### Redis
- **Port**: 6379
- **Persistence**: AOF enabled
- **Memory**: Configurable limit

#### RabbitMQ
- **Port**: 5672 (AMQP), 15672 (Management)
- **UI**: http://localhost:15672
- **Credentials**: admin/rabbit123

### Processing Services

#### Celery Workers
- **Queues**: ai_processing, notifications, cleanup, analytics
- **Concurrency**: 4 workers per queue
- **Monitoring**: Flower UI (optional)

#### AI Detection Service
- **Processing**: 10 FPS target
- **Models**: MediaPipe face detection
- **Storage**: Temporary frames only

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost/health

# Detailed health
curl http://localhost/api/health/detailed

# Readiness probe
curl http://localhost/api/health/ready

# Liveness probe
curl http://localhost/api/health/live
```

### Metrics

#### Prometheus
- **URL**: http://localhost:9090
- **Targets**: Auto-discovered services
- **Retention**: 200 hours

#### Grafana
- **URL**: http://localhost:3001
- **Credentials**: admin/grafana123
- **Dashboards**: Pre-configured

### Logging

#### Structured Logging
- **Format**: JSON (production), Console (development)
- **Level**: Configurable (INFO, DEBUG, ERROR)
- **Output**: Docker logs, file logging

#### Log Aggregation
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Filter logs
docker-compose logs backend | grep ERROR
```

## Scaling

### Horizontal Scaling

#### Backend API
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

#### Celery Workers
```bash
# Scale workers
docker-compose up -d --scale celery_worker=4
```

### Load Balancing

#### Nginx Configuration
- **Algorithm**: Least connections
- **Health Checks**: Active/passive
- **Failover**: Automatic

#### Database Scaling
- **MongoDB**: Replica set for high availability
- **Redis**: Cluster mode for scaling
- **RabbitMQ**: Clustered queues

## Security

### Network Security

#### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

#### SSL/TLS
- **Protocol**: TLS 1.2+
- **Ciphers**: Strong cipher suites
- **Certificates**: Auto-renewal with Let's Encrypt

### Application Security

#### Authentication
- **JWT**: Secure token-based auth
- **Expiration**: 30 minutes
- **Refresh**: Token rotation

#### Rate Limiting
- **Global**: 1000 requests/minute
- **Auth**: 5 requests/5 minutes
- **API**: 60 requests/minute

#### Input Validation
- **Sanitization**: All user inputs
- **File Upload**: Type and size validation
- **SQL Injection**: Parameterized queries

### Data Protection

#### Encryption
- **At Rest**: MongoDB encryption
- **In Transit**: TLS 1.2+
- **Files**: Optional S3 encryption

#### Privacy
- **PII**: Minimal collection
- **Retention**: Configurable cleanup
- **Compliance**: GDPR considerations

## Performance Optimization

### Database Optimization

#### MongoDB Indexes
```javascript
// Created automatically on startup
db.sessions.createIndex({"student_id": 1})
db.events.createIndex({"session_id": 1, "timestamp": -1})
db.ai_detections.createIndex({"suspicious_score": -1})
```

#### Redis Caching
- **Sessions**: User session data
- **API Responses**: 5-minute cache
- **Rate Limits**: Sliding window

### Application Optimization

#### AI Processing
- **Frame Skipping**: Process every 3rd frame
- **Resolution**: Optimal for detection
- **Batch Processing**: Queue-based

#### WebSocket Optimization
- **Connection Pooling**: Efficient management
- **Message Batching**: Reduce overhead
- **Compression**: Message compression

## Backup and Recovery

### Database Backups

#### MongoDB
```bash
# Create backup
docker-compose exec mongodb mongodump --out /backup

# Restore backup
docker-compose exec mongodb mongorestore /backup
```

#### Redis
```bash
# Create snapshot
docker-compose exec redis redis-cli BGSAVE

# Copy RDB file
docker cp proctoring_redis:/data/dump.rdb ./backup/
```

### File Storage

#### Local Storage
```bash
# Backup storage directory
tar -czf storage_backup.tar.gz backend/storage/
```

#### S3 Storage
```bash
# Sync to S3
aws s3 sync backend/storage/ s3://your-bucket/backup/
```

### Disaster Recovery

#### Recovery Steps
1. **Stop services**: `docker-compose down`
2. **Restore data**: Database and files
3. **Update configuration**: If needed
4. **Start services**: `docker-compose up -d`
5. **Verify**: Health checks

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs service_name

# Check resources
docker stats

# Restart service
docker-compose restart service_name
```

#### Database Connection
```bash
# Test MongoDB connection
docker-compose exec mongodb mongo --eval "db.adminCommand('ping')"

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check slow queries
docker-compose logs backend | grep "slow query"

# Monitor AI processing
curl http://localhost/api/health/detailed
```

### Debug Mode

#### Enable Debug Logging
```bash
# Update environment
echo "LOG_LEVEL=DEBUG" >> .env

# Restart services
docker-compose restart backend
```

#### Access Service Containers
```bash
# Access backend container
docker-compose exec backend bash

# Access database
docker-compose exec mongodb mongo
```

## Maintenance

### Regular Tasks

#### Daily
- **Check logs**: Error monitoring
- **Health checks**: Service status
- **Performance metrics**: Resource usage

#### Weekly
- **Backup verification**: Test restores
- **Security updates**: Patch management
- **Log rotation**: Disk space management

#### Monthly
- **Performance tuning**: Optimization
- **Capacity planning**: Resource scaling
- **Security audit**: Vulnerability assessment

### Updates

#### Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

#### Dependency Updates
```bash
# Update Python dependencies
docker-compose exec backend pip install --upgrade -r requirements.txt

# Rebuild services
docker-compose build backend
docker-compose up -d
```

## Support

### Monitoring Alerts

Set up alerts for:
- **Service downtime**: Health check failures
- **High resource usage**: CPU/Memory thresholds
- **Error rates**: Application errors
- **Security events**: Failed auth attempts

### Documentation

- **API docs**: Swagger/OpenAPI
- **Architecture**: System design
- **Runbooks**: Incident response

### Contact Information

- **Technical support**: support@yourdomain.com
- **Security issues**: security@yourdomain.com
- **Emergency**: emergency@yourdomain.com

---

## Appendix

### Port List

| Service | Port | Protocol | Purpose |
|----------|------|----------|---------|
| Nginx | 80, 443 | HTTP/HTTPS | Load balancer |
| Frontend | 3000 | HTTP | React app |
| Backend | 8000 | HTTP | FastAPI |
| MongoDB | 27017 | TCP | Database |
| Redis | 6379 | TCP | Cache |
| RabbitMQ | 5672, 15672 | TCP/HTTP | Message queue |
| Prometheus | 9090 | HTTP | Metrics |
| Grafana | 3001 | HTTP | Visualization |

### Environment Variables Reference

See `.env.example` for complete list of configurable variables.

### Docker Commands Reference

```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3

# Execute commands
docker-compose exec backend bash

# Monitor resources
docker stats
```

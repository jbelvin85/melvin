# Remote Server Setup Guide

## Overview
This guide helps you deploy Melvin on a remote test server where resources and network speed may be limited.

## Key Changes for Remote/Slow Servers

The following optimizations have been made to support slower hardware:

### 1. Extended Docker Healthcheck Timeouts
**File**: `docker-compose.yml`

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 5s
  timeout: 5s
  retries: 60           # Increased from 30 to 60 (300s total)
  start_period: 60s     # Increased from 30s to 60s
```

**What this means**:
- `start_period: 60s` - Gives API 60 seconds to start before health checks begin
- `retries: 60` - Allows up to 300 seconds (5 minutes) total for API to become healthy
- `timeout: 5s` - Each health check has 5 seconds to complete

### 2. Extended Script Wait Timeout
**File**: `scripts/melvin.sh`

```bash
wait_for_api() {
  local retries=120      # Increased from 60 to 120 (240 seconds total)
  local delay=2
  # ...
}
```

**What this means**:
- Total wait time: 120 attempts × 2 seconds = **240 seconds (4 minutes)**
- Progress messages every 10 attempts with elapsed time tracking

## Typical Timeline on Slow Servers

```
[+] Building                          30-60 seconds
    └─ pip install                    5-10 minutes (major time sink)
[+] Starting containers               5-30 seconds
[melvin] Waiting for API...
    └─ API initialization             30-60 seconds
    └─ Database creation              10-30 seconds
[melvin] API is healthy               ✓
```

**Total expected time**: 10-15 minutes on slow hardware

## Troubleshooting Timeouts

### If API still times out:

1. **Check actual API startup**:
```bash
./scripts/melvin.sh logs api
```

Look for errors like:
- `ImportError` - Missing dependencies
- `Database connection refused` - Postgres/Mongo not ready
- `Permission denied` - File/volume issues

2. **Verify CPU/Memory**:
```bash
docker stats
```

If CPU maxed out at 100%, the server is genuinely slow.

3. **Check disk space**:
```bash
df -h
```

If low on disk, pip install will be very slow.

4. **Increase timeouts further** (if needed):

Edit `docker-compose.yml`:
```yaml
healthcheck:
  start_period: 120s    # Double it
  retries: 120          # Double it
```

Edit `scripts/melvin.sh`:
```bash
local retries=240       # Double it
```

## Environment Variables for Slow Servers

Set these before running `launch`:

```bash
# Increase Docker build cache
export DOCKER_BUILDKIT=1

# Skip npm audit (can be slow)
export NODE_ENV=production
npm config set audit false

# Disable optional dependencies that might slow installation
export NODE_SKIP_PLATFORM_CHECK=1
```

## Network-Specific Issues

### Slow Downloads
If Scryfall data downloads are timing out:

```bash
# Download data files manually on a faster machine first
curl -o oracle-cards.json https://api.scryfall.com/bulk-data
# ... then transfer via scp/sftp to /data/raw/
```

### Poor Connectivity
The script will automatically try to download required data files. If this fails:

```bash
./scripts/melvin.sh launch
# When prompted for missing files, provide the path:
# Path: /data/raw/oracle-cards-20251221100301.json
```

## Docker Resource Limits

If the server is resource-constrained, edit `docker-compose.yml`:

```yaml
services:
  api:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Performance Tips

1. **Use SSD storage** for Docker volumes (much faster than HDD)
2. **Increase swap** if RAM is limited
3. **Close other services** to free up resources
4. **Run during off-hours** on shared servers
5. **Use `--build-arg`** to cache layers across builds

## Validation

Once deployed, verify everything works:

```bash
# Check API health
curl http://localhost:8001/api/health

# Check container status
docker-compose ps

# All should show "healthy" and "Up"
```

## Summary of Timeout Changes

| Parameter | Old Value | New Value | Impact |
|-----------|-----------|-----------|--------|
| Docker start_period | 30s | 60s | More time for API startup |
| Docker retries | 30 | 60 | 5 minutes total healthcheck time |
| Script retries | 60 | 120 | 4 minutes total wait time |
| **Total wait** | **2 min** | **4-5 min** | Accommodates slow servers |

These changes maintain compatibility with fast servers while supporting slower infrastructure.

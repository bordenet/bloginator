# Monitoring and Observability Guide

This guide covers monitoring, metrics collection, and observability features in Bloginator.

---

## Table of Contents

1. [Overview](#overview)
2. [Metrics Collection](#metrics-collection)
3. [Structured Logging](#structured-logging)
4. [Performance Tracking](#performance-tracking)
5. [Exporters](#exporters)
6. [Integration Examples](#integration-examples)
7. [Best Practices](#best-practices)

---

## Overview

Bloginator includes built-in monitoring and observability features:

- **Metrics Collection**: Track operation counts, durations, success/failure rates
- **Structured Logging**: JSON logging for log aggregation systems
- **Performance Tracking**: Automatic timing and resource usage tracking
- **Multiple Exporters**: Console, JSON, Prometheus formats
- **System Metrics**: CPU, memory, thread count monitoring

---

## Metrics Collection

### Viewing Metrics

```bash
# View metrics in console (pretty tables)
bloginator metrics

# Export as JSON
bloginator metrics --format json --output metrics.json

# Export in Prometheus format
bloginator metrics --format prometheus --output metrics.prom
```

### Collected Metrics

**Operation Metrics:**
- Total operation count
- Success/failure counts
- Duration statistics (min, max, avg)
- Operation-specific metadata

**System Metrics:**
- CPU usage percentage
- Memory usage (MB and percentage)
- Number of threads
- Uptime

### Programmatic Access

```python
from bloginator.monitoring import get_metrics_collector

# Get global metrics collector
collector = get_metrics_collector()

# Get summary
summary = collector.get_summary()
print(f"Total operations: {summary['total_operations']}")

# Get system metrics
system = collector.get_system_metrics()
print(f"Memory usage: {system['memory_mb']:.1f} MB")
```

---

## Structured Logging

### Configuration

```python
from bloginator.monitoring import configure_logging
from pathlib import Path

# Development: Rich console with colors
configure_logging(
    level="DEBUG",
    rich_console=True,
)

# Production: JSON logging to file
configure_logging(
    level="INFO",
    log_file=Path("/var/log/bloginator/app.log"),
    structured=True,
    rich_console=False,
)
```

### Using Loggers

```python
from bloginator.monitoring import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Processing document")
logger.warning("High memory usage detected")
logger.error("Failed to connect to LLM", exc_info=True)

# Structured logging with extra fields
logger.info(
    "Document processed",
    extra={
        "doc_id": "abc123",
        "duration": 1.23,
        "chunks": 45,
    }
)
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause shutdown

### Environment Variables

```bash
# Set log level
export BLOGINATOR_LOG_LEVEL=DEBUG

# Set log file
export BLOGINATOR_LOG_FILE=/var/log/bloginator/app.log

# Enable structured logging
export BLOGINATOR_LOG_STRUCTURED=true
```

---

## Performance Tracking

### Automatic Tracking

Operations are automatically tracked when using the CLI:

```bash
# These operations are automatically tracked
bloginator extract corpus/ -o extracted/
bloginator index extracted/ -o index/
bloginator search index/ "query"
bloginator outline --index index/ --keywords "topic"
bloginator draft --index index/ --outline outline.json -o draft.md
```

### Manual Tracking

Use the `@track_operation` decorator:

```python
from bloginator.monitoring import track_operation

@track_operation("custom_operation")
def process_data(data: list[str]) -> dict:
    # Your code here
    return {"processed": len(data)}

# Operation is automatically tracked
result = process_data(["a", "b", "c"])
```

### Manual Metrics Collection

```python
from bloginator.monitoring import get_metrics_collector

collector = get_metrics_collector()

# Start tracking
metrics = collector.start_operation(
    "custom_task",
    doc_count=10,
    user="alice",
)

try:
    # Do work
    process_documents()

    # Mark as successful
    collector.complete_operation(metrics, success=True)
except Exception as e:
    # Mark as failed
    collector.complete_operation(
        metrics,
        success=False,
        error=str(e),
    )
    raise
```

---

## Exporters

### Console Exporter

Pretty-printed tables for human consumption:

```python
from bloginator.monitoring import ConsoleExporter, get_metrics_collector
from rich.console import Console

collector = get_metrics_collector()
exporter = ConsoleExporter(Console())
exporter.export(collector)
```

Output:
```
Operation Metrics
┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Operation ┃ Count ┃ Success ┃ Failure ┃ Avg Duration ┃
┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ extract   │    10 │      10 │       0 │       0.234s │
└───────────┴───────┴─────────┴─────────┴──────────────┘
```

### JSON Exporter

Machine-readable JSON format:

```python
from bloginator.monitoring import JSONExporter, get_metrics_collector

collector = get_metrics_collector()
exporter = JSONExporter(indent=2)

# Export to string
json_str = exporter.export(collector)

# Export to file
from pathlib import Path
exporter.export_to_file(collector, Path("metrics.json"))
```

### Prometheus Exporter

Prometheus text format for scraping:

```python
from bloginator.monitoring import PrometheusExporter, get_metrics_collector

collector = get_metrics_collector()
exporter = PrometheusExporter()

# Export to file for Prometheus to scrape
from pathlib import Path
exporter.export_to_file(collector, Path("/var/lib/prometheus/bloginator.prom"))
```

Output:
```
# HELP bloginator_operations_total Total number of operations
# TYPE bloginator_operations_total counter
bloginator_operations_total{operation="extract"} 10
bloginator_operations_total{operation="index"} 5

# HELP bloginator_cpu_percent CPU usage percentage
# TYPE bloginator_cpu_percent gauge
bloginator_cpu_percent 12.34
```

---

## Integration Examples

### Prometheus + Grafana

**1. Export metrics periodically:**

```bash
#!/bin/bash
# export-metrics.sh

while true; do
  bloginator metrics --format prometheus --output /var/lib/prometheus/bloginator.prom
  sleep 60
done
```

**2. Configure Prometheus:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'bloginator'
    file_sd_configs:
      - files:
        - '/var/lib/prometheus/bloginator.prom'
    scrape_interval: 60s
```

**3. Create Grafana dashboard:**

- Import metrics from Prometheus
- Create panels for operation counts, durations, error rates
- Set up alerts for high error rates or slow operations

### ELK Stack (Elasticsearch, Logstash, Kibana)

**1. Configure structured logging:**

```python
from bloginator.monitoring import configure_logging
from pathlib import Path

configure_logging(
    level="INFO",
    log_file=Path("/var/log/bloginator/app.log"),
    structured=True,
)
```

**2. Configure Logstash:**

```ruby
# logstash.conf
input {
  file {
    path => "/var/log/bloginator/app.log"
    codec => json
  }
}

filter {
  # Add any custom filters
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "bloginator-%{+YYYY.MM.dd}"
  }
}
```

**3. Create Kibana visualizations:**

- Log volume over time
- Error rate trends
- Operation duration distributions
- Top error messages

### CloudWatch (AWS)

**1. Configure CloudWatch agent:**

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/bloginator/app.log",
            "log_group_name": "/aws/bloginator",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          }
        ]
      }
    }
  }
}
```

**2. Create CloudWatch alarms:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name bloginator-high-error-rate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace Bloginator \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### Custom Monitoring Dashboard

```python
from bloginator.monitoring import get_metrics_collector, JSONExporter
from pathlib import Path
import json

def export_dashboard_data():
    """Export metrics for custom dashboard."""
    collector = get_metrics_collector()
    exporter = JSONExporter()

    # Export to web-accessible location
    metrics_file = Path("/var/www/html/metrics.json")
    exporter.export_to_file(collector, metrics_file)

    # Add timestamp
    data = json.loads(metrics_file.read_text())
    data["exported_at"] = datetime.now().isoformat()
    metrics_file.write_text(json.dumps(data, indent=2))

# Run periodically
import schedule
schedule.every(1).minutes.do(export_dashboard_data)
```

---

## Best Practices

### 1. Set Appropriate Log Levels

```python
# Development
configure_logging(level="DEBUG", rich_console=True)

# Staging
configure_logging(level="INFO", log_file=Path("app.log"))

# Production
configure_logging(
    level="WARNING",
    log_file=Path("/var/log/bloginator/app.log"),
    structured=True,
)
```

### 2. Monitor Key Operations

Focus on operations that impact user experience:

- **Extract**: Document processing time
- **Index**: Indexing throughput
- **Search**: Query latency
- **Outline**: Generation time
- **Draft**: End-to-end generation time

### 3. Set Up Alerts

Alert on critical conditions:

- Error rate > 5%
- Average operation duration > 2x baseline
- Memory usage > 80%
- CPU usage > 90%
- Disk space < 10%

### 4. Track Business Metrics

Beyond technical metrics, track:

- Documents processed per day
- Successful generations per user
- Average draft quality scores
- LLM API costs
- User satisfaction ratings

### 5. Regular Review

- Review metrics weekly
- Identify performance trends
- Optimize slow operations
- Update alert thresholds
- Archive old metrics

### 6. Resource Limits

Set appropriate limits in production:

```yaml
# docker-compose.yml
services:
  bloginator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 7. Log Rotation

Prevent disk space issues:

```bash
# /etc/logrotate.d/bloginator
/var/log/bloginator/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 bloginator bloginator
    sharedscripts
    postrotate
        systemctl reload bloginator
    endscript
}
```

---

## Troubleshooting

### High Memory Usage

```python
# Check system metrics
from bloginator.monitoring import get_metrics_collector

collector = get_metrics_collector()
system = collector.get_system_metrics()
print(f"Memory: {system['memory_mb']:.1f} MB ({system['memory_percent']:.1f}%)")

# If high, check for:
# - Large corpus in memory
# - Memory leaks in long-running processes
# - Too many concurrent operations
```

### Slow Operations

```bash
# View operation durations
bloginator metrics

# Look for:
# - Operations with high avg_duration
# - Operations with high max_duration
# - Increasing duration trends
```

### Missing Metrics

```python
# Verify metrics are being collected
from bloginator.monitoring import get_metrics_collector

collector = get_metrics_collector()
print(f"Total operations: {len(collector.operations)}")

# If zero, ensure operations are using tracking:
# - CLI commands automatically track
# - Custom code needs @track_operation decorator
```

---

## API Reference

See the [Developer Guide](DEVELOPER_GUIDE.md) for detailed API documentation on:

- `MetricsCollector` class
- `configure_logging()` function
- `get_logger()` function
- `track_operation()` decorator
- Exporter classes

---

## Further Reading

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Developer Guide](DEVELOPER_GUIDE.md) - API documentation
- [User Guide](USER_GUIDE.md) - CLI usage
- [Prometheus Documentation](https://prometheus.io/docs/)
- [ELK Stack Guide](https://www.elastic.co/guide/)

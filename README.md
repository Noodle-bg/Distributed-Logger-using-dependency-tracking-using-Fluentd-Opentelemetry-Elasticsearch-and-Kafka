# Distributed Logging System

A scalable distributed logging system that provides centralized log management, tracing, and monitoring capabilities for microservices.

## Prerequisites

- Python 3.8+
- Apache Kafka & Zookeeper
- Two VMs with network connectivity
- Ubuntu 22.x Jammy Jellyfish

## System Architecture

- **VM1**: Runs microservices and Fluentd
- **VM2**: Runs Kafka broker, Elasticsearch, and monitoring services

## Installation Guide

### 1. Install Base Requirements (Both VMs)

```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install the distributed logger package
pip install -e .
```

### 2. Install Fluentd (VM1)

```bash
# Install libssl1.1 (prerequisite)
echo "deb http://security.ubuntu.com/ubuntu focal-security main" | sudo tee /etc/apt/sources.list.d/focal-security.list
sudo apt-get update
sudo apt-get install libssl1.1
sudo rm /etc/apt/sources.list.d/focal-security.list

# Install td-agent (Fluentd)
curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-td-agent4.sh | sudo sh

# Install Kafka plugin for Fluentd
sudo td-agent-gem install fluent-plugin-kafka
```

Update Fluentd configuration:
```bash
sudo nano /etc/td-agent/td-agent.conf
# Copy the td-agent.conf content from config/fluentd/
# Replace VM2_IP with your actual VM2 IP address
sudo systemctl restart td-agent
```

### 3. Install Elasticsearch (VM2)

```bash
# Install Elasticsearch
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update
sudo apt-get install elasticsearch

# Configure Elasticsearch
sudo nano /etc/elasticsearch/elasticsearch.yml
# Copy the elasticsearch.yml content from config/elasticsearch/
```

### 4. Install OpenTelemetry Collector (VM2)

```bash
# Download and install OpenTelemetry Collector
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.96.0/otelcol_0.96.0_linux_amd64.deb
sudo dpkg -i otelcol_0.96.0_linux_amd64.deb

# Configure OpenTelemetry
sudo nano /etc/otel/config.yaml
# Copy the otel-collector-config.yaml content from config/otel/
sudo systemctl restart otelcol
```

## Configuration Updates

### 1. Update Kafka Configuration (VM2)
```bash
sudo nano /usr/local/kafka/config/server.properties
# Update advertised.listeners=PLAINTEXT://YOUR_VM2_IP:9092
sudo systemctl restart kafka
```

### 2. Create Required Kafka Topics (VM2)
```bash
# Create topics
kafka-topics.sh --create --topic service_logs --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
kafka-topics.sh --create --topic trace_logs --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
kafka-topics.sh --create --topic heartbeat_logs --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

## Starting Services

### On VM2:
```bash
# Start Elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch

# Start OpenTelemetry collector
sudo systemctl start otelcol
sudo systemctl enable otelcol

# Start Kafka
sudo systemctl start kafka
sudo systemctl status kakfa

# Start Zookeeper
sudo systemctl start zookeeper
sudo systemctl status zookeeper
```

### On VM1:
```bash
# Start Fluentd
sudo systemctl start td-agent
sudo systemctl enable td-agent
```

## Using the Logger


```python
from distributed_logger import DistributedLogger

# Initialize logger
logger = DistributedLogger("MyService", dependencies=["ServiceA", "ServiceB"])

# Log different levels
logger.info("Application started")
logger.warn("High latency detected", response_time_ms=1500, threshold_limit_ms=1000)
logger.error("Operation failed", error_code="ERR_001", error_message="Database timeout")

# Log service calls
logger.log_service_call("ServiceA", success=True)

# Clean up
logger.cleanup()  # Call this when shutting down
```

## Running Setup
```bash
# On VM_2
# Make sure kafka, opentelemetry, zookeeper and elasticsearch are running
# Terminal 1
python elasticsearch_consumer.py
# Terminal 2
python alert_system.py
```
```bash
# On VM_1
# Make sure td-agent is running
# In different Terminals
python service_a.py # Start Service A
python service_b.py  # Start Service B
python service_c.py  # Start Service C
...
python test_client.py
```

## Verifying Setup

1. Check Elasticsearch:
```bash
curl -X GET "localhost:9200/_cluster/health?pretty"
```

2. Check Fluentd logs:
```bash
sudo tail -f /var/log/td-agent/td-agent.log
```

3. Monitor Kafka topics:
```bash
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic service_logs --from-beginning
```

## Monitoring

- Elasticsearch data: http://VM2_IP:9200/_cat/indices
- Fluentd status: `sudo systemctl status td-agent`
- Kafka topics: `kafka-topics.sh --list --bootstrap-server localhost:9092`

## What We Aim In the Future
- Setup a more robust system to handle trace information across machines to keep track of complex layouts and dependencies between microservices
- Implement visualisation on elasticsearch using ELK stack using Kibana



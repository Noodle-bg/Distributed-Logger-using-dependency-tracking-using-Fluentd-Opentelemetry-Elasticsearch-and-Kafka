#!/bin/bash
# setup_kafka_topics.sh - Run this on VM2

# Create topics with appropriate configurations
/usr/local/kafka/bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic service_logs \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete

/usr/local/kafka/bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic trace_logs \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=259200000 \
    --config cleanup.policy=delete

/usr/local/kafka/bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic heartbeat_logs \
    --partitions 1 \
    --replication-factor 1 \
    --config retention.ms=86400000 \
    --config cleanup.policy=delete

# Verify topics
/usr/local/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Display topic details
/usr/local/kafka/bin/kafka-topics.sh --describe --bootstrap-server localhost:9092
# tests/test_kafka_producer.py
from kafka import KafkaProducer
import json
from datetime import datetime
import time
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestLogProducer:
    def __init__(self, kafka_broker: str):
        self.producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

    def produce_test_logs(self, num_messages: int = 5):
        """Generate test logs"""
        for i in range(num_messages):
            # Service log
            service_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "service_name": f"test-service-{i}",
                "log_level": "INFO",
                "message": f"Test log message {i}",
                "node_id": f"node-{i}",
                "log_id": f"log-{i}"
            }
            
            # Send to Kafka
            self.producer.send('service_logs', service_log)
            logger.info(f"Sent service log {i}")

            # Trace log
            trace_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": f"trace-{i}",
                "span_id": f"span-{i}",
                "source_service": "service-a",
                "target_service": "service-b",
                "operation": "test-operation",
                "duration_ms": 100.0,
                "status": "success"
            }
            
            self.producer.send('trace_logs', trace_log)
            logger.info(f"Sent trace log {i}")
            
            time.sleep(1)  # Wait between messages

        self.producer.flush()
        logger.info("Finished sending test messages")

if __name__ == "__main__":
    producer = TestLogProducer("localhost:9092")
    producer.produce_test_logs()
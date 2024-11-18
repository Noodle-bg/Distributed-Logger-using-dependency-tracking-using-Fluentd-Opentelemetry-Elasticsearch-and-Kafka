# tools/monitor_kafka.py

from kafka import KafkaConsumer
import json
import logging
from elasticsearch import Elasticsearch
from datetime import datetime
import time
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaMonitor:
    def __init__(self, kafka_broker: str = 'localhost:9092', es_host: str = 'http://localhost:9200'):
        self.consumers = {
            'service_logs': KafkaConsumer(
                'service_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest'
            ),
            'trace_logs': KafkaConsumer(
                'trace_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest'
            )
        }
        self.es = Elasticsearch([es_host])
    
    def print_message(self, topic: str, message: Dict[str, Any]):
        """Pretty print message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n{'-'*80}")
        print(f"Time: {timestamp}")
        print(f"Topic: {topic}")
        print(f"Content:")
        print(json.dumps(message, indent=2))
        print(f"{'-'*80}\n")
    
    def monitor_topics(self):
        """Monitor both Kafka topics"""
        try:
            logger.info("Starting Kafka monitor...")
            logger.info("Press Ctrl+C to stop")
            
            # Track statistics
            stats = {
                'service_logs': 0,
                'trace_logs': 0,
                'last_check': time.time()
            }
            
            while True:
                # Check service logs
                for msg in self.consumers['service_logs'].poll(timeout_ms=1000).values():
                    for m in msg:
                        self.print_message('service_logs', m.value)
                        stats['service_logs'] += 1
                
                # Check trace logs
                for msg in self.consumers['trace_logs'].poll(timeout_ms=1000).values():
                    for m in msg:
                        self.print_message('trace_logs', m.value)
                        stats['trace_logs'] += 1
                
                # Print stats every 5 seconds
                now = time.time()
                if now - stats['last_check'] >= 5:
                    # Check Elasticsearch
                    es_service_count = self.es.count(index='service-logs')['count']
                    es_trace_count = self.es.count(index='trace-logs')['count']
                    
                    print("\nStatistics:")
                    print(f"Service Logs: Kafka={stats['service_logs']}, Elasticsearch={es_service_count}")
                    print(f"Trace Logs: Kafka={stats['trace_logs']}, Elasticsearch={es_trace_count}")
                    print(f"{'-'*80}")
                    
                    stats['last_check'] = now
                
        except KeyboardInterrupt:
            logger.info("Stopping monitor...")
        finally:
            for consumer in self.consumers.values():
                consumer.close()

if __name__ == "__main__":
    monitor = KafkaMonitor()
    monitor.monitor_topics()
# elasticsearch_consumer.py

from elasticsearch import Elasticsearch
from kafka import KafkaConsumer
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchConsumer:
    def __init__(self, kafka_broker: str, elasticsearch_host: str):
        """Initialize the consumer"""
        self.es = Elasticsearch([elasticsearch_host])
        
        # Create Kafka consumers for each topic
        self.consumers = {
            'service_logs': KafkaConsumer(
                'service_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            ),
            'heartbeat_logs': KafkaConsumer(
                'heartbeat_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
        }
        
        # Create indices if they don't exist
        self._create_indices()
        
    def _create_indices(self):
        """Create Elasticsearch indices with appropriate mappings"""
        # Service logs mapping
        service_logs_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "service_name": {"type": "keyword"},
                    "log_level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "message_type": {"type": "keyword"},
                    "node_id": {"type": "keyword"},
                    "trace_id": {"type": "keyword"},
                    "error_details": {
                        "properties": {
                            "error_code": {"type": "keyword"},
                            "error_message": {"type": "text"}
                        }
                    },
                    "response_time_ms": {"type": "float"},
                    "threshold_limit_ms": {"type": "float"}
                }
            }
        }
        
        # Heartbeat logs mapping
        heartbeat_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "service_name": {"type": "keyword"},
                    "node_id": {"type": "keyword"},
                    "message_type": {"type": "keyword"},
                    "status": {"type": "keyword"}
                }
            }
        }
        
        # Create indices if they don't exist
        if not self.es.indices.exists(index='service_logs'):
            self.es.indices.create(index='service_logs', body=service_logs_mapping)
            logger.info("Created service_logs index")
            
        if not self.es.indices.exists(index='heartbeat_logs'):
            self.es.indices.create(index='heartbeat_logs', body=heartbeat_mapping)
            logger.info("Created heartbeat_logs index")

    def _format_timestamp(self, log_data: dict) -> dict:
        """Ensure timestamp is in correct format"""
        if 'timestamp' in log_data:
            try:
                # Try to parse the timestamp
                datetime.fromisoformat(log_data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, convert to ISO format
                log_data['timestamp'] = datetime.fromisoformat(
                    log_data['timestamp']
                ).isoformat()
        return log_data

    def process_messages(self):
        """Process messages from all topics"""
        try:
            logger.info("Starting to consume messages...")
            
            # Process service logs
            for message in self.consumers['service_logs']:
                try:
                    log_data = self._format_timestamp(message.value)
                    self.es.index(
                        index='service_logs',
                        document=log_data
                    )
                    logger.debug(f"Indexed service log: {log_data.get('message', '')}")
                except Exception as e:
                    logger.error(f"Error processing service log: {e}")

            # Process heartbeat logs
            for message in self.consumers['heartbeat_logs']:
                try:
                    log_data = self._format_timestamp(message.value)
                    self.es.index(
                        index='heartbeat_logs',
                        document=log_data
                    )
                    logger.debug(f"Indexed heartbeat for service: {log_data.get('service_name', '')}")
                except Exception as e:
                    logger.error(f"Error processing heartbeat: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        finally:
            self.close()

    def close(self):
        """Clean up resources"""
        for consumer in self.consumers.values():
            consumer.close()
        self.es.close()
        logger.info("Closed all connections")

if __name__ == "__main__":
    # Configuration
    KAFKA_BROKER = "localhost:9092"
    ELASTICSEARCH_HOST = "http://localhost:9200"
    
    # Create and run consumer
    consumer = ElasticsearchConsumer(KAFKA_BROKER, ELASTICSEARCH_HOST)
    consumer.process_messages()
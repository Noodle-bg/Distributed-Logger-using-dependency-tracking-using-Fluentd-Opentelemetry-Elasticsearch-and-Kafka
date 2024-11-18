# test_kafka_connection.py
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_kafka_connection():
    try:
        # Try to create a producer
        producer = KafkaProducer(
            bootstrap_servers=['192.168.244.130:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Try to send a test message
        future = producer.send('service_logs', {'test': 'message'})
        
        # Wait for the message to be sent
        record_metadata = future.get(timeout=10)
        
        logger.info(f"Message sent successfully to partition {record_metadata.partition} at offset {record_metadata.offset}")
        
        producer.close()
        return True
        
    except KafkaError as e:
        logger.error(f"Failed to connect to Kafka: {str(e)}")
        return False

if __name__ == "__main__":
    test_kafka_connection()
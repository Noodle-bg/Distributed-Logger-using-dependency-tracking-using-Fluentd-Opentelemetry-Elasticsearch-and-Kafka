# tests/test_alerts.py

from kafka import KafkaProducer
import json
import time
from datetime import datetime
import uuid
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertTester:
    def __init__(self, kafka_broker='localhost:9092'):
        self.producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        
    def generate_error_burst(self):
        """Generate burst of errors to trigger error rate alert"""
        logger.info("Generating error burst from Service B...")
        
        trace_id = str(uuid.uuid4())
        for i in range(6):  # Generate multiple errors quickly
            log = {
                "timestamp": datetime.utcnow().isoformat(),
                "service_name": "ServiceB",
                "node_id": f"node-b-1",
                "log_level": "ERROR",
                "message": f"Database connection failed - attempt {i+1}",
                "trace_id": trace_id,
                "error_details": {
                    "error_code": "DB_CONN_ERR",
                    "error_message": "Connection timeout"
                }
            }
            self.producer.send('service_logs', log)
            time.sleep(0.5)  # Small delay between errors

    def generate_cascade_failure(self):
        """Generate cascade failure scenario"""
        logger.info("Generating cascade failure scenario...")
        
        trace_id = str(uuid.uuid4())
        
        # Service B fails
        service_b_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "ServiceB",
            "node_id": "node-b-1",
            "log_level": "ERROR",
            "message": "Critical database failure",
            "trace_id": trace_id,
            "error_details": {
                "error_code": "DB_FATAL",
                "error_message": "Database corruption detected"
            }
        }
        self.producer.send('service_logs', service_b_log)
        
        # Service A fails because it depends on B
        service_a_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "ServiceA",
            "node_id": "node-a-1",
            "log_level": "ERROR",
            "message": "Failed to process request due to downstream service failure",
            "trace_id": trace_id,
            "error_details": {
                "error_code": "DEP_ERR",
                "error_message": "Dependency ServiceB unavailable"
            }
        }
        self.producer.send('service_logs', service_a_log)
        
        # Add trace information
        trace_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "span_id": str(uuid.uuid4()),
            "source_service": "ServiceA",
            "target_service": "ServiceB",
            "operation": "process_request",
            "duration_ms": 1500.0,
            "status": "error"
        }
        self.producer.send('trace_logs', trace_log)

    def generate_performance_degradation(self):
        """Generate performance degradation scenario"""
        logger.info("Generating performance degradation scenario...")
        
        # Generate several slow responses
        for i in range(4):
            trace_id = str(uuid.uuid4())
            response_time = random.uniform(1500, 3000)  # Between 1.5s and 3s
            
            log = {
                "timestamp": datetime.utcnow().isoformat(),
                "service_name": "ServiceC",
                "node_id": "node-c-1",
                "log_level": "WARN",
                "message": "Slow response detected",
                "trace_id": trace_id,
                "response_time_ms": response_time,
                "threshold_limit_ms": 1000
            }
            self.producer.send('service_logs', log)
            time.sleep(1)

    def simulate_service_downtime(self):
        """Simulate service becoming unresponsive"""
        logger.info("Simulating service downtime...")
        
        # First send a normal heartbeat
        heartbeat = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "ServiceB",
            "node_id": "node-b-1",
            "message_type": "HEARTBEAT",
            "status": "UP"
        }
        self.producer.send('service_logs', heartbeat)
        
        # Wait - during this time, no heartbeats will be sent
        logger.info("Waiting to simulate downtime...")
        time.sleep(35)  # Should trigger heartbeat missing alert

    def run_all_tests(self):
        """Run all test scenarios"""
        try:
            logger.info("Starting alert system tests...")
            
            # Run test scenarios
            self.generate_error_burst()
            time.sleep(5)
            
            self.generate_cascade_failure()
            time.sleep(5)
            
            self.generate_performance_degradation()
            time.sleep(5)
            
            self.simulate_service_downtime()
            
            # Ensure all messages are sent
            self.producer.flush()
            logger.info("All test scenarios completed")
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
        finally:
            self.producer.close()

if __name__ == "__main__":
    tester = AlertTester()
    tester.run_all_tests()
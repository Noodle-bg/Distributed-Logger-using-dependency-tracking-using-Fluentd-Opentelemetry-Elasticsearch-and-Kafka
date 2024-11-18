# alert_system/kafka_alert_monitor.py

from kafka import KafkaConsumer
import json
import time
from datetime import datetime
import logging
from typing import Dict, Set
from collections import defaultdict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaAlertMonitor:
    def __init__(self, kafka_broker: str = 'localhost:9092'):
        # Initialize consumers for both topics
        self.service_logs_consumer = KafkaConsumer(
            'service_logs',
            bootstrap_servers=[kafka_broker],
            group_id='alert_system_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        
        self.trace_logs_consumer = KafkaConsumer(
            'trace_logs',
            bootstrap_servers=[kafka_broker],
            group_id='alert_system_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest'
        )
        
        # State tracking
        self.service_states: Dict[str, Dict] = defaultdict(dict)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_heartbeat: Dict[str, datetime] = {}
        self.service_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Error window tracking (for error rate calculation)
        self.error_windows: Dict[str, list] = defaultdict(list)
        
        # Alert thresholds
        self.thresholds = {
            'error_rate': 5,  # errors per minute
            'response_time': 1000,  # ms
            'heartbeat_missing': 30,  # seconds
        }
    
    def monitor_service_logs(self):
        """Monitor service logs for issues"""
        logger.info("Starting service logs monitor...")
        for message in self.service_logs_consumer:
            log = message.value
            service_name = log.get('service_name')
            log_level = log.get('log_level')
            
            # Process based on log type
            if log_level == 'ERROR':
                self._handle_error(service_name, log)
            
            elif 'response_time_ms' in log:
                self._check_performance(service_name, log)
            
            elif log.get('message_type') == 'HEARTBEAT':
                self._update_heartbeat(service_name, log)
    
    def monitor_trace_logs(self):
        """Monitor trace logs for dependency issues"""
        logger.info("Starting trace logs monitor...")
        for message in self.trace_logs_consumer:
            trace = message.value
            source = trace.get('source_service')
            target = trace.get('target_service')
            status = trace.get('status')
            
            # Update dependency map
            if source and target:
                self.service_dependencies[source].add(target)
            
            # Check for cascade failures
            if status == 'error':
                self._check_cascade_failure(trace)
    
    def _handle_error(self, service: str, log: Dict):
        """Handle error logs and check error rates"""
        now = datetime.utcnow()
        self.error_windows[service].append(now)
        
        # Remove errors older than 1 minute
        self.error_windows[service] = [
            t for t in self.error_windows[service] 
            if (now - t).total_seconds() <= 60
        ]
        
        # Check error rate
        if len(self.error_windows[service]) >= self.thresholds['error_rate']:
            self._alert(
                "HIGH_ERROR_RATE",
                f"Service {service} has high error rate: {len(self.error_windows[service])} errors/min",
                service,
                log
            )
    
    def _check_performance(self, service: str, log: Dict):
        """Check for performance issues"""
        response_time = log.get('response_time_ms', 0)
        if response_time > self.thresholds['response_time']:
            self._alert(
                "SLOW_PERFORMANCE",
                f"Service {service} response time ({response_time}ms) exceeds threshold",
                service,
                log
            )
    
    def _update_heartbeat(self, service: str, log: Dict):
        """Update service heartbeat timestamp"""
        self.last_heartbeat[service] = datetime.utcnow()
    
    def _check_heartbeats(self):
        """Check for missing heartbeats"""
        while True:
            now = datetime.utcnow()
            for service, last_beat in self.last_heartbeat.items():
                if (now - last_beat).total_seconds() > self.thresholds['heartbeat_missing']:
                    self._alert(
                        "MISSING_HEARTBEAT",
                        f"Service {service} hasn't sent heartbeat in {self.thresholds['heartbeat_missing']} seconds",
                        service,
                        {"last_heartbeat": last_beat.isoformat()}
                    )
            time.sleep(5)
    
    def _check_cascade_failure(self, trace: Dict):
        """Check for cascade failures"""
        source = trace.get('source_service')
        target = trace.get('target_service')
        
        # Get all services that depend on the target
        affected_services = {
            svc for svc, deps in self.service_dependencies.items()
            if target in deps
        }
        
        if affected_services:
            self._alert(
                "CASCADE_FAILURE",
                f"Failure in {target} affecting dependent services",
                target,
                {
                    "affected_services": list(affected_services),
                    "trace_id": trace.get('trace_id')
                }
            )
    
    def _alert(self, alert_type: str, message: str, service: str, details: Dict):
        """Generate alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": alert_type,
            "service": service,
            "message": message,
            "details": details
        }
        logger.warning(f"ALERT: {json.dumps(alert, indent=2)}")
    
    def run(self):
        """Run the alert monitor"""
        try:
            logger.info("Starting alert monitor...")
            
            # Start monitoring threads
            service_thread = threading.Thread(
                target=self.monitor_service_logs, 
                daemon=True
            )
            trace_thread = threading.Thread(
                target=self.monitor_trace_logs, 
                daemon=True
            )
            heartbeat_thread = threading.Thread(
                target=self._check_heartbeats, 
                daemon=True
            )
            
            # Start all threads
            service_thread.start()
            trace_thread.start()
            heartbeat_thread.start()
            
            # Wait for threads
            service_thread.join()
            trace_thread.join()
            heartbeat_thread.join()
            
        except KeyboardInterrupt:
            logger.info("Shutting down alert monitor...")
        except Exception as e:
            logger.error(f"Error in alert monitor: {e}")
        finally:
            self.service_logs_consumer.close()
            self.trace_logs_consumer.close()

if __name__ == "__main__":
    monitor = KafkaAlertMonitor()
    monitor.run()
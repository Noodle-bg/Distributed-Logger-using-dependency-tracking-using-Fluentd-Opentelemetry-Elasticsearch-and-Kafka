# consumers/alert_system.py

from kafka import KafkaConsumer
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Set, List
import logging
from colorama import init, Fore, Style
import threading
import time

# Initialize colorama for colored terminal output
init()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self, kafka_broker: str):
        """Initialize the alert system"""
        self.kafka_broker = kafka_broker
        
        # Initialize Kafka consumers
        self.consumers = {
            'service_logs': KafkaConsumer(
                'service_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            ),
            'trace_logs': KafkaConsumer(
                'trace_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            ),
            'heartbeat_logs': KafkaConsumer(
                'heartbeat_logs',
                bootstrap_servers=[kafka_broker],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
        }
        
        # Track service dependencies
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Track service status
        self.service_status: Dict[str, Dict] = defaultdict(dict)
        
        # Track last heartbeat times
        self.last_heartbeat: Dict[str, datetime] = {}
        
        # Track cascading errors
        self.error_chains: Dict[str, List[str]] = {}
        
        # Start heartbeat monitor
        self._start_heartbeat_monitor()

    def _print_alert(self, level: str, service: str, message: str, details: str = None):
        """Print formatted alert to terminal"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = Fore.YELLOW if level == "WARN" else Fore.RED if level == "ERROR" else Fore.WHITE
        
        print(f"\n{color}[{timestamp}] {level} - {service}{Style.RESET_ALL}")
        print(f"└─ {message}")
        if details:
            print(f"   └─ {details}")

    def _monitor_heartbeats(self):
        """Monitor service heartbeats and generate alerts"""
        while True:
            current_time = datetime.now()
            for service, last_time in self.last_heartbeat.items():
                time_diff = current_time - last_time
                
                if time_diff > timedelta(seconds=45):  # Two missed heartbeats
                    self._print_alert(
                        "ERROR",
                        service,
                        "Service may be down - Multiple heartbeats missed",
                        f"Last heartbeat: {last_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                elif time_diff > timedelta(seconds=30):  # One missed heartbeat
                    self._print_alert(
                        "WARN",
                        service,
                        "Service heartbeat delayed",
                        f"Last heartbeat: {last_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            time.sleep(15)

    def _start_heartbeat_monitor(self):
        """Start heartbeat monitoring thread"""
        monitor_thread = threading.Thread(
            target=self._monitor_heartbeats,
            daemon=True
        )
        monitor_thread.start()

    def _update_dependencies(self, trace_data: dict):
        """Update service dependency graph"""
        source = trace_data.get('source_service')
        target = trace_data.get('target_service')
        
        if source and target:
            self.dependencies[source].add(target)

    def _track_cascading_error(self, trace_id: str, service: str, error_details: dict):
        """Track error propagation through services"""
        if trace_id not in self.error_chains:
            self.error_chains[trace_id] = []
        
        self.error_chains[trace_id].append({
            'service': service,
            'error': error_details
        })
        
        # If we have multiple errors in the chain, analyze them
        if len(self.error_chains[trace_id]) > 1:
            self._analyze_error_chain(trace_id)

    def _analyze_error_chain(self, trace_id: str):
        """Analyze error chain to identify root cause"""
        chain = self.error_chains[trace_id]
        
        # Find the deepest service in the dependency graph
        deepest_service = None
        max_depth = -1
        
        for error in chain:
            service = error['service']
            depth = 0
            
            # Calculate service depth in dependency graph
            for other_service, deps in self.dependencies.items():
                if service in deps:
                    depth += 1
            
            if depth > max_depth:
                max_depth = depth
                deepest_service = service
        
        if deepest_service:
            # Get the error details for the root cause
            root_error = next(
                (error['error'] for error in chain if error['service'] == deepest_service),
                None
            )
            
            if root_error:
                affected_services = [error['service'] for error in chain]
                self._print_alert(
                    "ERROR",
                    deepest_service,
                    f"Root cause of cascading failure affecting {', '.join(affected_services)}",
                    f"Error: {root_error.get('error_code', 'Unknown')} - {root_error.get('error_message', 'No message')}"
                )

    def process_messages(self):
        """Process messages from all topics"""
        try:
            logger.info("Starting alert system...")
            
            # Process service logs
            for message in self.consumers['service_logs']:
                log_data = message.value
                
                if log_data.get('log_level') in ['ERROR', 'WARN']:
                    level = log_data['log_level']
                    service = log_data['service_name']
                    msg = log_data['message']
                    
                    # Get error details if present
                    details = None
                    if 'error_details' in log_data:
                        details = (f"Error: {log_data['error_details'].get('error_code', 'Unknown')} - "
                                 f"{log_data['error_details'].get('error_message', 'No message')}")
                        
                        # Track error for cascade analysis
                        trace_id = log_data.get('trace_id')
                        if trace_id:
                            self._track_cascading_error(trace_id, service, log_data['error_details'])
                    
                    self._print_alert(level, service, msg, details)

            # Process trace logs
            for message in self.consumers['trace_logs']:
                trace_data = message.value
                self._update_dependencies(trace_data)
                
                if trace_data.get('status') == 'ERROR':
                    self._print_alert(
                        "ERROR",
                        f"{trace_data['source_service']} -> {trace_data['target_service']}",
                        "Service call failed",
                        f"Duration: {trace_data.get('duration_ms', 0)}ms"
                    )

            # Process heartbeat logs
            for message in self.consumers['heartbeat_logs']:
                heartbeat_data = message.value
                service = heartbeat_data['service_name']
                self.last_heartbeat[service] = datetime.now()
                
        except KeyboardInterrupt:
            logger.info("Shutting down alert system...")
        finally:
            self.close()

    def close(self):
        """Clean up resources"""
        for consumer in self.consumers.values():
            consumer.close()
        logger.info("Closed all connections")

if __name__ == "__main__":
    # Configuration
    KAFKA_BROKER = "localhost:9092"
    
    # Create and run alert system
    alert_system = AlertSystem(KAFKA_BROKER)
    alert_system.process_messages()
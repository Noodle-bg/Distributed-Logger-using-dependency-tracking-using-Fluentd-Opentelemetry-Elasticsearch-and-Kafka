# services/base_service.py

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import logging
from distributed_logger import BaseLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self, service_name: str, port: int, dependencies: List[str] = None):
        """
        Initialize service with BaseLogger integration
        """
        self.service_name = service_name
        self.port = port
        self.dependencies = dependencies or []
        
        # Initialize the BaseLogger instead of direct Fluentd connection
        self.logger = BaseLogger(
            service_name=service_name,
            dependencies=dependencies
        )
        
        # Log service startup
        self.logger.info(f"Service {service_name} starting up")
        if dependencies:
            self.logger.info(f"Registered dependencies: {', '.join(dependencies)}")

    def get_service_url(self, service_name: str) -> str:
        """Get URL for a service"""
        service_ports = {
            'ServiceA': 5000,
            'ServiceB': 5001,
            'ServiceC': 5002,
            'ServiceD': 5003,
            'ServiceE': 5004,
            'ServiceF': 5005,
            'ServiceG': 5006,
            'ServiceH': 5007
        }
        return f"http://localhost:{service_ports[service_name]}"

    def cleanup(self):
        """Cleanup service resources"""
        try:
            self.logger.info(f"Service {self.service_name} shutting down")
            self.logger.cleanup()
        except Exception as e:
            logger.error(f"Error during service cleanup: {e}")
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from distributed_logger import BaseLogger
import requests

class BaseService:
    def __init__(self, name: str, port: int, dependencies: list[str] = None):
        self.logger = BaseLogger(name, dependencies)
        self.port = port
        
    def get_service_url(self, service_name: str) -> str:
        service_ports = {
            "ServiceA": 5000,
            "ServiceB": 5001,
            "ServiceC": 5002,
            "ServiceD": 5003,
            "ServiceE": 5004,
            "ServiceF": 5005,
            "ServiceG": 5006,
            "ServiceH": 5007
        }
        return f"http://localhost:{service_ports[service_name]}"
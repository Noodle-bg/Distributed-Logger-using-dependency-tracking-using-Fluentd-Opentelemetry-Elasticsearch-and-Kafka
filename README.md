# RR-Team-63-distributed-logging-system

# Distributed Logging System - Week 1

## Overview
This is a distributed logging system that tracks interactions between microservices, maintains heartbeats, and logs various service activities. For Week 1, we have implemented basic logging functionality with three interconnected services.

## Project Structure
```
distributed-logging-system/
├── distributed_logger/         # Core logging package
│   ├── __init__.py
│   ├── base_logger.py         # Base logging functionality
│   └── dependency_tracker.py   # Dependency tracking logic
│
├── services/                   # Microservices
│   ├── base_service.py        # Base service class
│   ├── service_a.py           # Example service that calls B and C
│   ├── service_b.py           # Example independent service
│   ├── service_c.py           # Example independent service
│   └── run_service.py         # Script to run services
└── setup.py
```

## Setup Instructions

1. Install dependencies:
```bash
pip install flask requests
```

2. Install the distributed_logger package:
```bash
# From the root directory (where setup.py is)
pip install -e .
```

## How to Create a New Service

1. Create a new service file 

2. Update `run_service.py` to include your new service:
```python
def run_service(service_name: str):
    if service_name == "a":
        from service_a import create_app
    elif service_name == "b":
        from service_b import create_app
    elif service_name == "c":
        from service_c import create_app
    elif service_name == "new":  # Add your service
        from new_service import create_app
    else:
        print(f"Unknown service: {service_name}")
        return
        
    app = create_app()
    port = {
        "a": 5000, 
        "b": 5001, 
        "c": 5002,
        "new": 5004  # Add your service port
    }[service_name]
    
    app.run(host="localhost", port=port)
```

## Available Logging Functions

```python
# Info level logging
self.logger.info("Normal operation message")

# Warning level logging (for performance issues)
self.logger.warn(
    "Operation took longer than expected",
    response_time_ms=1500,
    threshold_limit_ms=1000
)

# Error level logging
self.logger.error(
    "Operation failed",
    error_code="ERROR_CODE",
    error_message="Detailed error message"
)

# Log service calls
self.logger.log_service_call(
    "TargetServiceName",
    success=True/False,
    error_details={  # Optional, for failed calls
        "error_code": "CODE",
        "error_message": "Message"
    }
)
```

## Running Services

1. Start individual services in separate terminals:
```bash
# Terminal 1
python run_service.py a

# Terminal 2
python run_service.py b

# Terminal 3
python run_service.py c

# Terminal 4 (for your new service)
python run_service.py new
```

2. Test your service by updating `test_client.py`


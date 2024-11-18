# config/settings.py

class VMConfig:
    # VM2 Configuration (Infrastructure)
    INFRASTRUCTURE_VM = {
        'host': '192.168.244.130',  # VM2's IP
        'kafka_port': 9092,
        'elasticsearch_port': 9200
    }

    # VM1 Configuration (Services)
    SERVICES_VM = {
        'host': '192.168.244.129',  # VM1's IP
        'service_ports': {
            'service_a': 5000,
            'service_b': 5001,
            'service_c': 5002
        }
    }

    # Kafka Configuration
    KAFKA_CONFIG = {
        'bootstrap_servers': f"{INFRASTRUCTURE_VM['host']}:{INFRASTRUCTURE_VM['kafka_port']}",
        'topics': {
            'service_logs': 'service_logs',
            'trace_logs': 'trace_logs'
        }
    }

    # Elasticsearch Configuration
    ELASTICSEARCH_CONFIG = {
        'host': f"http://{INFRASTRUCTURE_VM['host']}:{ELASTICSEARCH_CONFIG['elasticsearch_port']}"
    }
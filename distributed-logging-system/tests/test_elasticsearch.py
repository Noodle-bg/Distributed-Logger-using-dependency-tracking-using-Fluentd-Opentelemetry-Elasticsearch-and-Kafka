# test_elasticsearch.py
from elasticsearch import Elasticsearch
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_elasticsearch_setup():
    """Test basic Elasticsearch functionality"""
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])
        
        # 1. Check if Elasticsearch is responding
        if not es.ping():
            logger.error("Could not connect to Elasticsearch")
            return False
        
        logger.info("Successfully connected to Elasticsearch")
        
        # 2. Create test index with proper mapping
        index_name = "test-logs"
        
        # Define mapping with correct date format
        mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "service": {"type": "keyword"},
                    "message": {"type": "text"},
                    "level": {"type": "keyword"}
                }
            }
        }
        
        # Delete index if it exists
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            logger.info(f"Deleted existing index: {index_name}")
        
        # Create new index
        es.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index: {index_name}")
        
        # 3. Insert test document
        doc = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "service": "test-service",
            "message": "Test log message",
            "level": "INFO"
        }
        
        response = es.index(index=index_name, document=doc)
        logger.info(f"Indexed document with ID: {response['_id']}")
        
        # 4. Wait for document to be indexed
        es.indices.refresh(index=index_name)
        
        # 5. Search for the document
        result = es.search(
            index=index_name,
            query={
                "match": {
                    "message": "Test log message"
                }
            }
        )
        
        hits = result['hits']['total']['value']
        logger.info(f"Found {hits} matching documents")
        
        # Print the found document
        if hits > 0:
            doc = result['hits']['hits'][0]['_source']
            logger.info(f"Retrieved document: {doc}")
        
        # 6. Clean up
        es.indices.delete(index=index_name)
        logger.info("Test index deleted")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Elasticsearch: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Make sure Elasticsearch is installed
    try:
        import elasticsearch
    except ImportError:
        logger.error("Elasticsearch package not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "elasticsearch"])
    
    success = test_elasticsearch_setup()
    if success:
        logger.info("All tests passed!")
    else:
        logger.error("Tests failed!")
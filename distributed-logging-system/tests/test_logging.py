from distributed_logger import DistributedLogger
import time
import random
import uuid

def simulate_service_call(logger, target_service, should_fail=False):
    """Simulate a service call with timing and tracing"""
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    
    # Start trace
    logger.record_trace(
        operation=f"call_{target_service}_start",
        trace_id=trace_id
    )
    
    time.sleep(random.uniform(0.1, 0.5))  # Simulate processing time
    duration_ms = int((time.time() - start_time) * 1000)
    
    if should_fail:
        error_details = {
            "error_code": "SIMULATED_ERROR",
            "error_message": f"Simulated failure calling {target_service}",
            "duration_ms": duration_ms
        }
        logger.log_service_call(target_service, success=False, error_details=error_details)
        
        # Record error trace
        logger.record_trace(
            operation=f"call_{target_service}_error",
            trace_id=trace_id,
            duration_ms=duration_ms,
            error=error_details
        )
    else:
        logger.log_service_call(target_service, success=True)
        
        # Record success trace
        logger.record_trace(
            operation=f"call_{target_service}_complete",
            trace_id=trace_id,
            duration_ms=duration_ms
        )

def run_comprehensive_test():
    logger = DistributedLogger("TestService", ["ServiceA", "ServiceB"])
    
    print("1. Testing basic logging...")
    logger.info("Application starting up")
    logger.warn("System resources running low", 
                response_time_ms=1500, 
                threshold_limit_ms=1000)
    logger.error("Database connection failed",
                error_code="DB_ERROR",
                error_message="Connection timeout")

    print("2. Testing service call tracing...")
    simulate_service_call(logger, "ServiceA")
    simulate_service_call(logger, "ServiceB", should_fail=True)
    
    print("3. Testing service chain...")
    trace_id = str(uuid.uuid4())
    logger.record_trace("chain_start", trace_id=trace_id)
    
    simulate_service_call(logger, "ServiceA")
    time.sleep(0.1)
    simulate_service_call(logger, "ServiceB")
    
    logger.record_trace("chain_complete", trace_id=trace_id)
    
    print("4. Testing performance logging...")
    start_time = time.time()
    time.sleep(0.5)
    duration = int((time.time() - start_time) * 1000)
    
    logger.warn("Slow operation detected", 
                response_time_ms=duration,
                threshold_limit_ms=200)
    
    logger.record_trace(
        "slow_operation",
        duration_ms=duration,
        error={"threshold_exceeded": True} if duration > 200 else None
    )

if __name__ == "__main__":
    print("Starting comprehensive logging test...")
    run_comprehensive_test()
    print("Waiting for messages to be processed...")
    time.sleep(2)
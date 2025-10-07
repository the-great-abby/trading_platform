#!/usr/bin/env python3
"""
Fix Service Dependencies and Circuit Breakers
Improves reliability of service calls with better error handling, caching, and circuit breakers
"""

import logging
from pathlib import Path
import re
import asyncio
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceDependencyFixer:
    """Fix service dependencies and improve circuit breakers"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.strategies_dir = self.base_dir / "src" / "strategies"
        self.services_dir = self.base_dir / "src" / "services"
        
    def fix_all_service_dependencies(self):
        """Fix service dependencies across all files"""
        logger.info("🔧 Fixing service dependencies and circuit breakers...")
        
        # Fix strategies
        self.fix_strategy_service_dependencies()
        
        # Fix service files
        self.fix_service_files()
        
        # Create enhanced circuit breaker utility
        self.create_circuit_breaker_utility()
        
        logger.info("✅ Service dependency fixes completed")
    
    def fix_strategy_service_dependencies(self):
        """Fix service dependencies in strategy files"""
        logger.info("🔧 Fixing strategy service dependencies...")
        
        strategy_files = [
            "enhanced_elliott_wave_strategies.py",
            "service_based_elliott_wave_strategy.py",
            "advanced/adaptive_sector_wave_strategy.py"
        ]
        
        for file_name in strategy_files:
            file_path = self.strategies_dir / file_name
            if file_path.exists():
                self.add_service_resilience_to_strategy(file_path)
            else:
                logger.warning(f"⚠️ Strategy file not found: {file_path}")
    
    def add_service_resilience_to_strategy(self, file_path: Path):
        """Add service resilience to a strategy file"""
        logger.info(f"🔧 Adding service resilience to {file_path.name}...")
        
        content = file_path.read_text()
        
        # Add circuit breaker imports if not present
        if "from src.services.circuit_breaker import CircuitBreaker" not in content:
            # Find the imports section
            import_section = re.search(r'(from.*?import.*?\n)+', content)
            if import_section:
                imports_end = import_section.end()
                new_imports = """
from src.services.circuit_breaker import CircuitBreaker
from src.services.service_health_monitor import ServiceHealthMonitor
"""
                content = content[:imports_end] + new_imports + content[imports_end:]
        
        # Add circuit breaker initialization to __init__ method
        init_pattern = r'(def __init__\(self[^)]*\):.*?)(super\(\)\.__init__\([^)]*\))'
        if re.search(init_pattern, content, re.DOTALL):
            content = re.sub(
                init_pattern,
                r'\1\2\n        \n        # Service resilience\n        self.circuit_breaker = CircuitBreaker(\n            failure_threshold=3,\n            recovery_timeout=30,\n            expected_exception=Exception\n        )\n        self.service_health_monitor = ServiceHealthMonitor()',
                content,
                flags=re.DOTALL
            )
        
        # Add service call wrapper method
        service_wrapper = '''
    async def _safe_service_call(self, service_name: str, call_func, *args, **kwargs):
        """Make a safe service call with circuit breaker protection"""
        try:
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.warning(f"🚫 Circuit breaker OPEN for {service_name}")
                return None
            
            # Make the call
            result = await call_func(*args, **kwargs)
            
            # Record success
            self.circuit_breaker.record_success()
            self.service_health_monitor.record_success(service_name)
            
            return result
            
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            self.service_health_monitor.record_failure(service_name, str(e))
            
            logger.error(f"❌ Service call failed for {service_name}: {e}")
            return None
'''
        
        # Add the wrapper method before the last class method
        if "async def _safe_service_call" not in content:
            # Find a good place to insert it (before the last method)
            last_method_match = re.search(r'(\n    async def [^_].*?)(\nclass|\n$)', content, re.DOTALL)
            if last_method_match:
                insert_point = last_method_match.start(1)
                content = content[:insert_point] + service_wrapper + content[insert_point:]
        
        file_path.write_text(content)
        logger.info(f"✅ Added service resilience to {file_path.name}")
    
    def fix_service_files(self):
        """Fix service files for better reliability"""
        logger.info("🔧 Fixing service files...")
        
        # Fix LLM service timeout issues
        llm_service_path = self.services_dir / "llm_service" / "service.py"
        if llm_service_path.exists():
            self.fix_llm_service_timeouts(llm_service_path)
        
        # Fix database connection issues
        db_service_path = self.services_dir / "live_trading" / "database.py"
        if db_service_path.exists():
            self.fix_database_connections(db_service_path)
    
    def fix_llm_service_timeouts(self, file_path: Path):
        """Fix LLM service timeout issues"""
        logger.info(f"🔧 Fixing LLM service timeouts in {file_path.name}...")
        
        content = file_path.read_text()
        
        # Add timeout handling
        timeout_fix = '''
        # Enhanced timeout handling
        self.timeout_handler = EnhancedTimeoutHandler()
        self.timeout_handler.register_timeout_callback('llm_service', self._handle_llm_timeout)
        
        # Circuit breaker for LLM calls
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
'''
        
        # Insert after LLM client initialization
        if "self.llm_client = None" in content and "Enhanced timeout handling" not in content:
            content = content.replace(
                "self.llm_client = None",
                f"self.llm_client = None{timeout_fix}"
            )
        
        # Add timeout handler method
        timeout_handler_method = '''
    async def _handle_llm_timeout(self, operation: str, request_data: Dict[str, Any]):
        """Handle LLM service timeout"""
        logger.warning(f"⏰ LLM service timeout for operation: {operation}")
        
        # Return a safe default response
        return {
            'status': 'timeout',
            'message': 'LLM service timeout - using fallback response',
            'data': {'confidence': 0.5, 'recommendation': 'HOLD'},
            'timestamp': datetime.now().isoformat()
        }
'''
        
        if "async def _handle_llm_timeout" not in content:
            # Insert before the last method
            last_method = re.search(r'(\n    async def [^_].*?)(\nclass|\n$)', content, re.DOTALL)
            if last_method:
                insert_point = last_method.start(1)
                content = content[:insert_point] + timeout_handler_method + content[insert_point:]
        
        file_path.write_text(content)
        logger.info(f"✅ Fixed LLM service timeouts in {file_path.name}")
    
    def fix_database_connections(self, file_path: Path):
        """Fix database connection issues"""
        logger.info(f"🔧 Fixing database connections in {file_path.name}...")
        
        content = file_path.read_text()
        
        # Add connection retry logic
        retry_logic = '''
# Enhanced database connection with retry logic
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_db_session_with_retry() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with retry logic"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
'''
        
        if "get_db_session_with_retry" not in content:
            # Insert after the existing get_db_session function
            content = content.replace(
                "async def get_db_session() -> AsyncGenerator[AsyncSession, None]:",
                f"async def get_db_session() -> AsyncGenerator[AsyncSession, None]:{retry_logic}\n\nasync def get_db_session() -> AsyncGenerator[AsyncSession, None]:"
            )
        
        file_path.write_text(content)
        logger.info(f"✅ Fixed database connections in {file_path.name}")
    
    def create_circuit_breaker_utility(self):
        """Create enhanced circuit breaker utility"""
        logger.info("🔧 Creating circuit breaker utility...")
        
        circuit_breaker_path = self.services_dir / "circuit_breaker.py"
        
        circuit_breaker_code = '''#!/usr/bin/env python3
"""
Enhanced Circuit Breaker Implementation
Provides robust circuit breaker functionality for service calls
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Enhanced circuit breaker with exponential backoff and health monitoring"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception,
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        
        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution"""
        self.total_calls += 1
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("🔄 Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record a successful call"""
        self.total_successes += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("✅ Circuit breaker CLOSED - service recovered")
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        self.total_failures += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"🚫 Circuit breaker OPEN - {self.failure_count} failures")
        
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("🚫 Circuit breaker OPEN - failure in half-open state")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure >= timedelta(seconds=self.recovery_timeout)
    
    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection"""
        if not self.can_execute():
            raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise e
        except Exception as e:
            self.record_failure()
            raise e

class ServiceHealthMonitor:
    """Monitor service health and provide metrics"""
    
    def __init__(self):
        self.service_metrics = {}
        self.health_check_interval = 60  # seconds
        self.last_health_check = {}
    
    def record_success(self, service_name: str):
        """Record a successful service call"""
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'last_success': None,
                'last_failure': None,
                'average_response_time': 0.0
            }
        
        metrics = self.service_metrics[service_name]
        metrics['total_calls'] += 1
        metrics['successful_calls'] += 1
        metrics['last_success'] = datetime.now()
    
    def record_failure(self, service_name: str, error: str):
        """Record a failed service call"""
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'last_success': None,
                'last_failure': None,
                'average_response_time': 0.0
            }
        
        metrics = self.service_metrics[service_name]
        metrics['total_calls'] += 1
        metrics['failed_calls'] += 1
        metrics['last_failure'] = datetime.now()
        
        logger.warning(f"❌ Service {service_name} failed: {error}")
    
    def get_service_health(self, service_name: str) -> dict:
        """Get health metrics for a service"""
        if service_name not in self.service_metrics:
            return {'status': 'unknown', 'metrics': {}}
        
        metrics = self.service_metrics[service_name]
        success_rate = metrics['successful_calls'] / metrics['total_calls'] if metrics['total_calls'] > 0 else 0
        
        return {
            'status': 'healthy' if success_rate > 0.8 else 'unhealthy',
            'success_rate': success_rate,
            'metrics': metrics
        }
    
    def get_all_service_health(self) -> dict:
        """Get health metrics for all services"""
        return {service: self.get_service_health(service) for service in self.service_metrics.keys()}
'''
        
        circuit_breaker_path.write_text(circuit_breaker_code)
        logger.info(f"✅ Created circuit breaker utility at {circuit_breaker_path}")
        
        # Create service health monitor
        health_monitor_path = self.services_dir / "service_health_monitor.py"
        health_monitor_code = '''#!/usr/bin/env python3
"""
Service Health Monitor
Monitors the health of all trading system services
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    """Monitor health of all trading system services"""
    
    def __init__(self):
        self.services = {
            'elliott-wave-service': 'http://localhost:11001/health',
            'options-data-service': 'http://localhost:11002/health',
            'market-data-service': 'http://localhost:11003/health',
            'llm-service': 'http://localhost:12001/health',
            'backtest-service': 'http://localhost:10001/health'
        }
        self.health_status = {}
        self.last_check = {}
        
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        logger.info("🔍 Checking health of all services...")
        
        tasks = []
        for service_name, health_url in self.services.items():
            task = asyncio.create_task(self._check_service_health(service_name, health_url))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            if isinstance(result, Exception):
                self.health_status[service_name] = {
                    'status': 'unhealthy',
                    'error': str(result),
                    'last_check': datetime.now()
                }
            else:
                self.health_status[service_name] = result
        
        return self.health_status
    
    async def _check_service_health(self, service_name: str, health_url: str) -> Dict[str, Any]:
        """Check health of a single service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response.raise_for_status()
                
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'last_check': datetime.now()
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Service {service_name} health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now()
            }
    
    def get_service_status(self, service_name: str) -> str:
        """Get status of a specific service"""
        if service_name not in self.health_status:
            return 'unknown'
        
        return self.health_status[service_name].get('status', 'unknown')
    
    def get_unhealthy_services(self) -> list:
        """Get list of unhealthy services"""
        return [service for service, status in self.health_status.items() 
                if status.get('status') == 'unhealthy']
    
    async def wait_for_service_recovery(self, service_name: str, max_wait: int = 300) -> bool:
        """Wait for a service to recover"""
        logger.info(f"⏳ Waiting for {service_name} to recover...")
        
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < max_wait:
            await self._check_service_health(service_name, self.services[service_name])
            
            if self.get_service_status(service_name) == 'healthy':
                logger.info(f"✅ {service_name} recovered!")
                return True
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        logger.warning(f"⏰ Timeout waiting for {service_name} to recover")
        return False
'''
        
        health_monitor_path.write_text(health_monitor_code)
        logger.info(f"✅ Created service health monitor at {health_monitor_path}")

async def main():
    fixer = ServiceDependencyFixer()
    fixer.fix_all_service_dependencies()

if __name__ == "__main__":
    asyncio.run(main())





"""
Load testing script for HealthInsightCore API
Tests system performance under various load conditions
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTestResult:
    """Container for load test results"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
    
    def add_result(self, response_time: float, status_code: int, error: str = None):
        """Add a single request result"""
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        self.total_requests += 1
        
        if error:
            self.errors.append(error)
            self.failed_requests += 1
        else:
            if 200 <= status_code < 400:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics"""
        if not self.response_times:
            return {"error": "No response times recorded"}
        
        duration = self.end_time - self.start_time
        requests_per_second = self.total_requests / duration if duration > 0 else 0
        
        return {
            "test_duration_seconds": round(duration, 2),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate_percent": round((self.successful_requests / self.total_requests) * 100, 2),
            "requests_per_second": round(requests_per_second, 2),
            "response_times": {
                "min_ms": round(min(self.response_times), 2),
                "max_ms": round(max(self.response_times), 2),
                "avg_ms": round(statistics.mean(self.response_times), 2),
                "median_ms": round(statistics.median(self.response_times), 2),
                "p95_ms": round(self._percentile(self.response_times, 95), 2),
                "p99_ms": round(self._percentile(self.response_times, 99), 2)
            },
            "status_code_distribution": self._get_status_distribution(),
            "error_count": len(self.errors),
            "unique_errors": len(set(self.errors)) if self.errors else 0
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = int(index)
            upper = lower + 1
            weight = index - lower
            return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def _get_status_distribution(self) -> Dict[str, int]:
        """Get HTTP status code distribution"""
        distribution = {}
        for code in set(self.status_codes):
            distribution[str(code)] = self.status_codes.count(code)
        return distribution


class LoadTester:
    """Load testing utility for API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                return {
                    "response_time_ms": response_time,
                    "status_code": response.status,
                    "data": response_data,
                    "error": None
                }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "response_time_ms": response_time,
                "status_code": 0,
                "data": None,
                "error": str(e)
            }
    
    async def run_concurrent_requests(
        self,
        method: str,
        endpoint: str,
        concurrent_users: int,
        requests_per_user: int,
        **request_kwargs
    ) -> LoadTestResult:
        """Run concurrent requests to test load"""
        result = LoadTestResult()
        result.start_time = time.time()
        
        async def user_session():
            """Simulate a single user making multiple requests"""
            for _ in range(requests_per_user):
                response = await self.make_request(method, endpoint, **request_kwargs)
                result.add_result(
                    response["response_time_ms"],
                    response["status_code"],
                    response["error"]
                )
        
        # Create tasks for concurrent users
        tasks = [user_session() for _ in range(concurrent_users)]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        result.end_time = time.time()
        return result
    
    async def run_ramp_up_test(
        self,
        method: str,
        endpoint: str,
        max_users: int,
        ramp_up_duration: int,
        test_duration: int,
        **request_kwargs
    ) -> LoadTestResult:
        """Run a ramp-up load test"""
        result = LoadTestResult()
        result.start_time = time.time()
        
        users_per_second = max_users / ramp_up_duration
        active_tasks = []
        
        async def user_loop():
            """Continuous request loop for a user"""
            while time.time() - result.start_time < test_duration:
                response = await self.make_request(method, endpoint, **request_kwargs)
                result.add_result(
                    response["response_time_ms"],
                    response["status_code"],
                    response["error"]
                )
                await asyncio.sleep(1)  # 1 request per second per user
        
        # Ramp up users gradually
        for second in range(ramp_up_duration):
            # Add new users
            new_users = int(users_per_second)
            for _ in range(new_users):
                task = asyncio.create_task(user_loop())
                active_tasks.append(task)
            
            await asyncio.sleep(1)
        
        # Wait for test duration to complete
        remaining_time = test_duration - (time.time() - result.start_time)
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)
        
        # Cancel all active tasks
        for task in active_tasks:
            task.cancel()
        
        # Wait for tasks to finish cancellation
        await asyncio.gather(*active_tasks, return_exceptions=True)
        
        result.end_time = time.time()
        return result


async def test_health_endpoint(base_url: str, concurrent_users: int = 10, requests_per_user: int = 10):
    """Test the health endpoint under load"""
    logger.info(f"Testing health endpoint with {concurrent_users} concurrent users, {requests_per_user} requests each")
    
    async with LoadTester(base_url) as tester:
        result = await tester.run_concurrent_requests(
            "GET", "/health", concurrent_users, requests_per_user
        )
        
        summary = result.get_summary()
        logger.info("Health endpoint test results:")
        logger.info(json.dumps(summary, indent=2))
        
        return summary


async def test_database_intensive_endpoint(base_url: str, concurrent_users: int = 5, requests_per_user: int = 5):
    """Test database-intensive endpoints"""
    logger.info(f"Testing database endpoints with {concurrent_users} concurrent users, {requests_per_user} requests each")
    
    # Test endpoints that hit the database
    endpoints_to_test = [
        ("GET", "/api/v1/reports/"),
        ("GET", "/api/v1/metrics/tracked"),
        ("GET", "/api/v1/search/reports/history")
    ]
    
    results = {}
    
    async with LoadTester(base_url) as tester:
        for method, endpoint in endpoints_to_test:
            logger.info(f"Testing {method} {endpoint}")
            
            # Note: These endpoints require authentication in real scenarios
            # For load testing, you might need to mock authentication or use test tokens
            result = await tester.run_concurrent_requests(
                method, endpoint, concurrent_users, requests_per_user,
                headers={"Authorization": "Bearer test-token"}  # Mock token
            )
            
            summary = result.get_summary()
            results[f"{method} {endpoint}"] = summary
            
            logger.info(f"Results for {method} {endpoint}:")
            logger.info(json.dumps(summary, indent=2))
    
    return results


async def test_memory_usage_under_load(base_url: str):
    """Test memory usage under sustained load"""
    import psutil
    import os
    
    logger.info("Testing memory usage under sustained load")
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    async with LoadTester(base_url) as tester:
        # Run sustained load for 2 minutes
        result = await tester.run_ramp_up_test(
            "GET", "/health",
            max_users=20,
            ramp_up_duration=30,  # 30 seconds to ramp up
            test_duration=120     # 2 minutes total
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        summary = result.get_summary()
        summary["memory_usage"] = {
            "initial_mb": round(initial_memory, 2),
            "final_mb": round(final_memory, 2),
            "increase_mb": round(memory_increase, 2),
            "increase_percent": round((memory_increase / initial_memory) * 100, 2)
        }
        
        logger.info("Memory usage test results:")
        logger.info(json.dumps(summary, indent=2))
        
        return summary


async def run_comprehensive_load_test(base_url: str):
    """Run a comprehensive load test suite"""
    logger.info("Starting comprehensive load test suite")
    
    test_results = {}
    
    # Test 1: Basic health endpoint
    test_results["health_endpoint"] = await test_health_endpoint(base_url, 20, 10)
    
    # Test 2: Database endpoints (with lower load due to complexity)
    test_results["database_endpoints"] = await test_database_intensive_endpoint(base_url, 5, 3)
    
    # Test 3: Memory usage under sustained load
    test_results["memory_usage"] = await test_memory_usage_under_load(base_url)
    
    # Test 4: Spike test - sudden high load
    logger.info("Running spike test")
    async with LoadTester(base_url) as tester:
        spike_result = await tester.run_concurrent_requests(
            "GET", "/health", 50, 5  # 50 concurrent users, 5 requests each
        )
        test_results["spike_test"] = spike_result.get_summary()
    
    # Generate overall report
    logger.info("=== COMPREHENSIVE LOAD TEST RESULTS ===")
    logger.info(json.dumps(test_results, indent=2))
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"load_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"Results saved to {filename}")
    
    return test_results


async def main():
    """Main function to run load tests"""
    parser = argparse.ArgumentParser(description="Load test HealthInsightCore API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--test-type", choices=["health", "database", "memory", "comprehensive"], 
                       default="comprehensive", help="Type of test to run")
    parser.add_argument("--concurrent-users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--requests-per-user", type=int, default=10, help="Requests per user")
    
    args = parser.parse_args()
    
    if args.test_type == "health":
        await test_health_endpoint(args.base_url, args.concurrent_users, args.requests_per_user)
    elif args.test_type == "database":
        await test_database_intensive_endpoint(args.base_url, args.concurrent_users, args.requests_per_user)
    elif args.test_type == "memory":
        await test_memory_usage_under_load(args.base_url)
    else:
        await run_comprehensive_load_test(args.base_url)


if __name__ == "__main__":
    asyncio.run(main())
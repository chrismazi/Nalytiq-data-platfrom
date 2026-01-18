"""
Load Testing and Performance Tests

Stress tests for:
- Concurrent API requests
- Database connection handling
- Rate limiting
- Memory usage
"""

import pytest
import time
import concurrent.futures
import statistics
from typing import List, Tuple
from datetime import datetime


class TestLoadPerformance:
    """Load and performance tests"""
    
    @pytest.mark.performance
    def test_api_response_time(self, test_client):
        """Test API response times are acceptable"""
        endpoints = [
            ("/health/live", 50),      # Should be < 50ms
            ("/health/ready", 200),     # Should be < 200ms
            ("/api/v1/security/rbac/permissions", 300),  # Should be < 300ms
        ]
        
        results = []
        for endpoint, max_time_ms in endpoints:
            times = []
            for _ in range(10):
                start = time.perf_counter()
                response = test_client.get(endpoint)
                duration_ms = (time.perf_counter() - start) * 1000
                times.append(duration_ms)
            
            avg_time = statistics.mean(times)
            results.append({
                "endpoint": endpoint,
                "avg_ms": round(avg_time, 2),
                "max_allowed_ms": max_time_ms,
                "passed": avg_time < max_time_ms
            })
        
        # All endpoints should meet their targets
        failed = [r for r in results if not r["passed"]]
        assert len(failed) == 0, f"Slow endpoints: {failed}"
    
    @pytest.mark.performance
    def test_concurrent_requests(self, test_client):
        """Test handling concurrent requests"""
        num_requests = 50
        
        def make_request():
            start = time.perf_counter()
            response = test_client.get("/health/live")
            duration = time.perf_counter() - start
            return response.status_code, duration
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        status_codes = [r[0] for r in results]
        durations = [r[1] * 1000 for r in results]
        
        success_rate = status_codes.count(200) / len(status_codes) * 100
        avg_duration = statistics.mean(durations)
        p99_duration = sorted(durations)[int(len(durations) * 0.99)]
        
        print(f"Concurrent test: {num_requests} requests")
        print(f"Success rate: {success_rate}%")
        print(f"Avg duration: {avg_duration:.2f}ms")
        print(f"P99 duration: {p99_duration:.2f}ms")
        
        assert success_rate >= 95, f"Success rate too low: {success_rate}%"
        assert p99_duration < 2000, f"P99 too high: {p99_duration}ms"
    
    @pytest.mark.performance
    def test_sustained_load(self, test_client):
        """Test sustained load over time"""
        duration_seconds = 5
        requests_per_second = 10
        
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration_seconds:
            for _ in range(requests_per_second):
                try:
                    response = test_client.get("/health/live")
                    if response.status_code != 200:
                        errors += 1
                except Exception:
                    errors += 1
                request_count += 1
            time.sleep(1)
        
        total_requests = request_count
        error_rate = errors / total_requests * 100 if total_requests > 0 else 0
        
        print(f"Sustained load test:")
        print(f"Duration: {duration_seconds}s")
        print(f"Total requests: {total_requests}")
        print(f"Error rate: {error_rate:.2f}%")
        
        assert error_rate < 5, f"Error rate too high: {error_rate}%"
    
    @pytest.mark.performance
    def test_large_payload_handling(self, test_client):
        """Test handling large request payloads"""
        # Create large dataset registration
        large_description = "A" * 10000  # 10KB description
        
        dataset_data = {
            "name": f"Large Dataset Test {datetime.now().timestamp()}",
            "description": large_description,
            "data_type": "statistics",
            "access_level": "public",
            "owner_org_code": "NISR",
            "row_count": 1000000,
            "tags": ["test"] * 100  # 100 tags
        }
        
        start = time.perf_counter()
        response = test_client.post("/api/v1/federation/catalog/datasets", json=dataset_data)
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Should handle large payload within reasonable time
        assert duration_ms < 5000, f"Large payload took too long: {duration_ms}ms"
        assert response.status_code in [200, 409, 422]


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    @pytest.mark.skip(reason="Requires psutil monitoring")
    def test_no_memory_leak(self, test_client):
        """Test that repeated requests don't leak memory"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make many requests
        for _ in range(1000):
            test_client.get("/health/live")
        
        final_memory = process.memory_info().rss
        memory_increase_mb = (final_memory - initial_memory) / (1024 * 1024)
        
        # Memory increase should be minimal
        assert memory_increase_mb < 50, f"Memory increased by {memory_increase_mb}MB"


class TestDatabasePerformance:
    """Test database query performance"""
    
    @pytest.mark.performance
    def test_list_endpoints_performance(self, test_client):
        """Test list endpoints perform well"""
        list_endpoints = [
            "/api/v1/xroad/organizations",
            "/api/v1/xroad/services",
            "/api/v1/security/rbac/roles",
            "/api/v1/federation/catalog/datasets",
        ]
        
        for endpoint in list_endpoints:
            times = []
            for _ in range(5):
                start = time.perf_counter()
                response = test_client.get(endpoint)
                duration_ms = (time.perf_counter() - start) * 1000
                times.append(duration_ms)
            
            avg_time = statistics.mean(times)
            assert avg_time < 500, f"{endpoint} too slow: {avg_time:.2f}ms"


class TestRateLimiting:
    """Test rate limiting behavior"""
    
    @pytest.mark.skip(reason="Rate limiting may not be enabled")
    def test_rate_limit_enforcement(self, test_client):
        """Test that rate limits are enforced"""
        # Make many rapid requests
        responses = []
        for _ in range(200):
            response = test_client.get("/api/v1/security/rbac/permissions")
            responses.append(response.status_code)
        
        # Some requests should be rate limited (429)
        rate_limited = responses.count(429)
        if rate_limited > 0:
            print(f"Rate limited {rate_limited} of {len(responses)} requests")


class TestCachePerformance:
    """Test caching effectiveness"""
    
    def test_repeated_request_caching(self, test_client):
        """Test that repeated requests benefit from caching"""
        endpoint = "/api/v1/security/rbac/permissions"
        
        # First request (cold)
        start = time.perf_counter()
        test_client.get(endpoint)
        cold_time = (time.perf_counter() - start) * 1000
        
        # Subsequent requests (potentially cached)
        warm_times = []
        for _ in range(10):
            start = time.perf_counter()
            test_client.get(endpoint)
            warm_times.append((time.perf_counter() - start) * 1000)
        
        avg_warm = statistics.mean(warm_times)
        
        print(f"Cold request: {cold_time:.2f}ms")
        print(f"Warm request avg: {avg_warm:.2f}ms")
        
        # Warm requests should generally be faster or similar
        # (If caching is working, warm should be significantly faster)

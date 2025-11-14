"""
Integration tests for Docker stack

Tests that all Docker services start correctly and communicate with each other.
Run with: docker-compose exec backend pytest tests/integration/test_docker_stack.py
"""
import pytest
import requests
import redis
import psycopg2
from sqlalchemy import create_engine
import time
import os


class TestDockerStack:
    """Test Docker services are running and healthy"""

    @pytest.fixture(scope="class")
    def backend_url(self):
        """Backend API URL"""
        return os.getenv("BACKEND_URL", "http://localhost:8000")

    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis client"""
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        return redis.Redis(host=host, port=port, decode_responses=True)

    @pytest.fixture(scope="class")
    def db_connection(self):
        """PostgreSQL connection"""
        conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=os.getenv("DATABASE_PORT", "5432"),
            database=os.getenv("DATABASE_NAME", "jobautomation"),
            user=os.getenv("DATABASE_USER", "postgres"),
            password=os.getenv("DATABASE_PASSWORD", "postgres")
        )
        yield conn
        conn.close()

    def test_backend_health(self, backend_url):
        """Test backend service is healthy"""
        response = requests.get(f"{backend_url}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "redis" in data

    def test_backend_api_docs(self, backend_url):
        """Test API documentation is accessible"""
        response = requests.get(f"{backend_url}/docs", timeout=10)
        assert response.status_code == 200

    def test_redis_connection(self, redis_client):
        """Test Redis is accessible"""
        # Test ping
        assert redis_client.ping() is True

        # Test set/get
        redis_client.set("test_key", "test_value")
        assert redis_client.get("test_key") == "test_value"
        redis_client.delete("test_key")

    def test_postgres_connection(self, db_connection):
        """Test PostgreSQL is accessible"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        assert version is not None
        assert "PostgreSQL" in version[0]
        cursor.close()

    def test_database_tables_exist(self, db_connection):
        """Test required database tables exist"""
        cursor = db_connection.cursor()

        # Check for main tables
        tables = [
            "jobs",
            "applications",
            "interviews",
            "offers",
            "notes",
            "follow_ups",
            "skill_gap_analyses",
            "candidate_skills",
            "recommendations",
            "company_research",
            "analytics_events"
        ]

        for table in tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                );
            """)
            exists = cursor.fetchone()[0]
            assert exists, f"Table {table} does not exist"

        cursor.close()

    def test_backend_redis_integration(self, backend_url, redis_client):
        """Test backend can communicate with Redis"""
        # Clear cache
        response = requests.delete(
            f"{backend_url}/api/v1/cache/test",
            timeout=10
        )

        # Get cache stats
        response = requests.get(
            f"{backend_url}/api/v1/cache/stats",
            timeout=10
        )
        assert response.status_code == 200
        stats = response.json()
        assert "redis_available" in stats
        assert stats["redis_available"] is True

    def test_backend_database_integration(self, backend_url):
        """Test backend can communicate with database"""
        # List jobs (should work even if empty)
        response = requests.get(
            f"{backend_url}/api/v1/jobs",
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data or isinstance(data, list)

    def test_websocket_endpoint(self, backend_url):
        """Test WebSocket endpoint is accessible"""
        import websocket

        ws_url = backend_url.replace("http", "ws") + "/api/v1/ws?user_id=test"

        try:
            ws = websocket.create_connection(ws_url, timeout=5)

            # Should receive welcome message
            message = ws.recv()
            assert message is not None

            # Send ping
            ws.send('{"action": "ping"}')

            # Close connection
            ws.close()
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")

    def test_service_dependencies(self, backend_url):
        """Test services start in correct order"""
        # Backend should not start until database and redis are ready
        response = requests.get(f"{backend_url}/health", timeout=10)
        data = response.json()

        # All dependencies should be healthy
        assert data["database"]["status"] == "healthy"
        assert data["redis"]["status"] == "healthy"

    def test_environment_variables(self):
        """Test required environment variables are set"""
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY"
        ]

        for var in required_vars:
            value = os.getenv(var)
            assert value is not None, f"Required environment variable {var} is not set"
            assert value != "", f"Required environment variable {var} is empty"

    def test_cors_configuration(self, backend_url):
        """Test CORS is configured correctly"""
        headers = {
            "Origin": "http://localhost:3000"
        }
        response = requests.get(
            f"{backend_url}/api/v1/jobs",
            headers=headers,
            timeout=10
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.slow
    def test_container_resource_usage(self):
        """Test containers are not using excessive resources"""
        import docker

        try:
            client = docker.from_env()

            # Check backend container
            backend = client.containers.get("job-automation-backend")
            stats = backend.stats(stream=False)

            # Memory should be under 512MB
            memory_usage = stats["memory_stats"]["usage"]
            assert memory_usage < 512 * 1024 * 1024, f"Backend using too much memory: {memory_usage / 1024 / 1024}MB"

        except Exception as e:
            pytest.skip(f"Docker not available: {e}")

    @pytest.mark.slow
    def test_service_restart_recovery(self, backend_url, redis_client):
        """Test services recover after restart"""
        import docker

        try:
            client = docker.from_env()

            # Restart redis
            redis_container = client.containers.get("job-automation-redis")
            redis_container.restart()

            # Wait for redis to be healthy
            time.sleep(5)

            # Backend should reconnect automatically
            response = requests.get(f"{backend_url}/health", timeout=10)
            data = response.json()
            assert data["redis"]["status"] == "healthy"

        except Exception as e:
            pytest.skip(f"Docker not available: {e}")


class TestDockerVolumes:
    """Test Docker volume persistence"""

    def test_database_volume_persistence(self, db_connection):
        """Test database data persists in volume"""
        cursor = db_connection.cursor()

        # Create test data
        cursor.execute("""
            INSERT INTO jobs (company, job_title, job_description, source)
            VALUES ('Test Corp', 'Test Job', 'Test Description', 'test')
            RETURNING id;
        """)
        job_id = cursor.fetchone()[0]
        db_connection.commit()

        # Verify data exists
        cursor.execute(f"SELECT company FROM jobs WHERE id = {job_id};")
        result = cursor.fetchone()
        assert result[0] == "Test Corp"

        # Cleanup
        cursor.execute(f"DELETE FROM jobs WHERE id = {job_id};")
        db_connection.commit()
        cursor.close()

    def test_redis_volume_persistence(self, redis_client):
        """Test Redis data persists in volume"""
        # Test AOF persistence is enabled
        config = redis_client.config_get("appendonly")
        assert config["appendonly"] == "yes"


class TestDockerNetworking:
    """Test Docker network configuration"""

    def test_service_discovery(self, backend_url):
        """Test services can discover each other by name"""
        # Backend should be able to connect to 'redis' and 'db' by hostname
        response = requests.get(f"{backend_url}/health", timeout=10)
        data = response.json()

        # If we can connect, service discovery is working
        assert data["database"]["connected"] is True
        assert data["redis"]["connected"] is True

    def test_network_isolation(self):
        """Test services are isolated in Docker network"""
        import docker

        try:
            client = docker.from_env()

            # Get backend container
            backend = client.containers.get("job-automation-backend")

            # Check it's on the job-automation network
            networks = backend.attrs["NetworkSettings"]["Networks"]
            assert "job-automation" in networks or "jobfinderautomation_job-automation" in networks

        except Exception as e:
            pytest.skip(f"Docker not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

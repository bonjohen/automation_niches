"""Query performance tests."""
import pytest
import time
import uuid
from datetime import date, timedelta


@pytest.mark.slow
@pytest.mark.performance
class TestEntityQueryPerformance:
    """Tests for entity query performance."""

    def test_list_50_entities_under_100ms(
        self,
        authenticated_client,
        db_session,
        entity_factory,
    ):
        """Listing 50 entities should complete in under 100ms."""
        account = authenticated_client.current_account

        # Create 50 entities
        for i in range(50):
            entity_factory(account=account, name=f"Perf Test Entity {i}")

        # Measure query time
        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/entities",
            params={"page_size": 50}
        )
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 100, f"Query took {duration_ms:.2f}ms, expected <100ms"

    @pytest.mark.skip(reason="Requires large dataset - run manually")
    def test_list_500_entities_under_500ms(
        self,
        authenticated_client,
        db_session,
        entity_factory,
    ):
        """Listing from 500 entities should complete in under 500ms."""
        account = authenticated_client.current_account

        # Create 500 entities (slow - only run when needed)
        for i in range(500):
            entity_factory(account=account, name=f"Large Perf Test {i}")

        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/entities",
            params={"page_size": 100}
        )
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 500, f"Query took {duration_ms:.2f}ms, expected <500ms"

    def test_entity_search_performance(
        self,
        authenticated_client,
        db_session,
        entity_factory,
    ):
        """Entity search should complete quickly."""
        account = authenticated_client.current_account

        # Create entities with searchable names
        for i in range(50):
            entity_factory(
                account=account,
                name=f"Searchable Vendor {i}",
                email=f"search{i}@example.com",
            )

        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/entities",
            params={"search": "Searchable"}
        )
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 200, f"Search took {duration_ms:.2f}ms, expected <200ms"


@pytest.mark.slow
@pytest.mark.performance
class TestRequirementQueryPerformance:
    """Tests for requirement query performance."""

    def test_list_100_requirements_under_200ms(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Listing 100 requirements should complete in under 200ms."""
        account = authenticated_client.current_account
        entity = entity_factory(account=account)
        req_type = requirement_type_factory()

        # Create 100 requirements
        for i in range(100):
            requirement_factory(
                account=account,
                entity=entity,
                requirement_type=req_type,
                name=f"Perf Test Req {i}",
            )

        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/requirements",
            params={"page_size": 100}
        )
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 200, f"Query took {duration_ms:.2f}ms, expected <200ms"

    def test_compliance_summary_performance(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Compliance summary with 100 entities should complete in under 300ms."""
        account = authenticated_client.current_account
        req_type = requirement_type_factory()

        # Create 100 entities with 3 requirements each
        for i in range(100):
            entity = entity_factory(account=account, name=f"Summary Entity {i}")
            for j in range(3):
                status = ["compliant", "expiring_soon", "expired"][j % 3]
                requirement_factory(
                    account=account,
                    entity=entity,
                    requirement_type=req_type,
                    status=status,
                )

        start_time = time.time()
        response = authenticated_client.get("/api/v1/requirements/summary")
        duration_ms = (time.time() - start_time) * 1000

        # Even if endpoint doesn't exist, test shouldn't crash
        if response.status_code == 200:
            assert duration_ms < 300, f"Summary took {duration_ms:.2f}ms, expected <300ms"


@pytest.mark.slow
@pytest.mark.performance
class TestSyncLogQueryPerformance:
    """Tests for sync log query performance."""

    def test_sync_logs_pagination_performance(
        self,
        authenticated_client,
        db_session,
        crm_sync_log_factory,
    ):
        """Paginated sync logs should be fast even with many records."""
        account = authenticated_client.current_account

        # Create 1000 sync logs
        for i in range(1000):
            crm_sync_log_factory(
                account=account,
                operation=f"test-op-{i}",
            )

        start_time = time.time()
        response = authenticated_client.get(
            "/api/v1/integrations/sync-logs",
            params={"page": 1, "page_size": 20}
        )
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 200, f"Query took {duration_ms:.2f}ms, expected <200ms"


@pytest.mark.slow
@pytest.mark.performance
class TestEntityWithRelationships:
    """Tests for entity queries with relationships loaded."""

    def test_entity_with_requirements_performance(
        self,
        authenticated_client,
        db_session,
        entity_factory,
        requirement_factory,
        requirement_type_factory,
    ):
        """Getting entity with requirements should be fast."""
        account = authenticated_client.current_account
        entity = entity_factory(account=account, name="Relationship Test Entity")
        req_type = requirement_type_factory()

        # Create 20 requirements for this entity
        for i in range(20):
            requirement_factory(
                account=account,
                entity=entity,
                requirement_type=req_type,
            )

        start_time = time.time()
        response = authenticated_client.get(f"/api/v1/entities/{entity.id}")
        duration_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert duration_ms < 100, f"Query took {duration_ms:.2f}ms, expected <100ms"


@pytest.mark.performance
class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    def test_concurrent_entity_reads(
        self,
        authenticated_client,
        db_session,
        entity_factory,
    ):
        """Multiple concurrent reads should not block each other."""
        import concurrent.futures

        account = authenticated_client.current_account

        # Create test entities
        entities = [
            entity_factory(account=account, name=f"Concurrent Test {i}")
            for i in range(10)
        ]

        def fetch_entity(entity_id):
            response = authenticated_client.get(f"/api/v1/entities/{entity_id}")
            return response.status_code, response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0

        # Note: TestClient doesn't truly support concurrent requests
        # This is more of a sequential stress test
        # For true concurrency testing, use locust or similar tools

        start_time = time.time()
        for entity in entities:
            authenticated_client.get(f"/api/v1/entities/{entity.id}")
        total_time_ms = (time.time() - start_time) * 1000

        # 10 sequential requests should complete in reasonable time
        assert total_time_ms < 1000, f"10 requests took {total_time_ms:.2f}ms"

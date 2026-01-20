"""
Load testing scenarios using Locust.

Run with:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 to configure and start the test.
"""
from locust import HttpUser, task, between
import random
import uuid


class ComplianceUser(HttpUser):
    """
    Simulates a typical user interacting with the compliance platform.

    Tasks are weighted to simulate realistic usage patterns:
    - Most requests are read operations (list, get)
    - Occasional write operations (create, update)
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None
    entity_ids = []

    def on_start(self):
        """Login and get auth token before starting tasks."""
        # Try to login with test credentials
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "loadtest@example.com",
                "password": "loadtestpassword123",
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
        else:
            # Try to register first
            self.client.post(
                "/api/v1/auth/register",
                json={
                    "email": "loadtest@example.com",
                    "password": "loadtestpassword123",
                    "first_name": "Load",
                    "last_name": "Test",
                    "company_name": "Load Test Company",
                }
            )
            # Then login
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": "loadtest@example.com",
                    "password": "loadtestpassword123",
                }
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")

    @property
    def headers(self):
        """Get headers with auth token."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(5)
    def list_entities(self):
        """List entities - most common operation."""
        self.client.get("/api/v1/entities", headers=self.headers)

    @task(3)
    def list_entities_with_search(self):
        """List entities with search filter."""
        search_terms = ["vendor", "contractor", "service", "test"]
        self.client.get(
            "/api/v1/entities",
            params={"search": random.choice(search_terms)},
            headers=self.headers
        )

    @task(3)
    def list_entities_paginated(self):
        """List entities with pagination."""
        self.client.get(
            "/api/v1/entities",
            params={"page": random.randint(1, 5), "page_size": 20},
            headers=self.headers
        )

    @task(2)
    def get_single_entity(self):
        """Get a single entity by ID."""
        if self.entity_ids:
            entity_id = random.choice(self.entity_ids)
            self.client.get(f"/api/v1/entities/{entity_id}", headers=self.headers)

    @task(3)
    def list_requirements(self):
        """List requirements."""
        self.client.get("/api/v1/requirements", headers=self.headers)

    @task(2)
    def list_requirements_by_status(self):
        """List requirements filtered by status."""
        statuses = ["pending", "compliant", "expiring_soon", "expired"]
        self.client.get(
            "/api/v1/requirements",
            params={"status": random.choice(statuses)},
            headers=self.headers
        )

    @task(1)
    def get_compliance_summary(self):
        """Get compliance summary/dashboard data."""
        self.client.get("/api/v1/requirements/summary", headers=self.headers)

    @task(1)
    def list_notifications(self):
        """List notifications."""
        self.client.get("/api/v1/notifications", headers=self.headers)

    @task(1)
    def create_entity(self):
        """Create a new entity."""
        response = self.client.post(
            "/api/v1/entities",
            json={
                "name": f"Load Test Vendor {uuid.uuid4().hex[:8]}",
                "email": f"vendor-{uuid.uuid4().hex[:8]}@loadtest.com",
                "phone": "(555) 000-0000",
            },
            headers=self.headers
        )

        if response.status_code == 201:
            entity_id = response.json().get("id")
            if entity_id:
                self.entity_ids.append(entity_id)
                # Keep list manageable
                if len(self.entity_ids) > 100:
                    self.entity_ids = self.entity_ids[-50:]

    @task(1)
    def get_integration_settings(self):
        """Get CRM integration settings."""
        self.client.get("/api/v1/integrations/settings", headers=self.headers)

    @task(1)
    def get_sync_logs(self):
        """Get CRM sync logs."""
        self.client.get(
            "/api/v1/integrations/sync-logs",
            params={"page": 1, "page_size": 20},
            headers=self.headers
        )


class HeavyUser(HttpUser):
    """
    Simulates a power user doing more intensive operations.
    Use sparingly in load tests.
    """

    wait_time = between(2, 5)
    token = None
    weight = 1  # Less frequent than ComplianceUser

    def on_start(self):
        """Login before starting."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "heavyuser@example.com",
                "password": "heavyuserpassword123",
            }
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @property
    def headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(1)
    def bulk_entity_list(self):
        """Request large page of entities."""
        self.client.get(
            "/api/v1/entities",
            params={"page_size": 100},
            headers=self.headers
        )

    @task(1)
    def search_all_statuses(self):
        """Search requirements across all statuses."""
        for status in ["pending", "compliant", "expiring_soon", "expired"]:
            self.client.get(
                "/api/v1/requirements",
                params={"status": status},
                headers=self.headers
            )

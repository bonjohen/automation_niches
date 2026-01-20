"""Multi-tenant data isolation tests."""
import pytest
import uuid


@pytest.mark.integration
class TestEntityIsolation:
    """Tests for entity data isolation between accounts."""

    def test_entity_query_filters_by_account(
        self, authenticated_client, account_factory, entity_factory, db_session
    ):
        """Entities should only be visible to their own account."""
        # Create a second account with its own entity
        other_account = account_factory(name="Other Company", slug="other-company")
        other_entity = entity_factory(
            account=other_account,
            name="Other Entity",
            email="other@example.com",
        )

        # Create entity for current user's account
        my_entity = entity_factory(
            account=authenticated_client.current_account,
            name="My Entity",
            email="mine@example.com",
        )

        # List entities should only return current user's entities
        response = authenticated_client.get("/api/v1/entities")

        assert response.status_code == 200
        data = response.json()

        entity_ids = [e["id"] for e in data.get("items", data)]
        assert str(my_entity.id) in entity_ids
        assert str(other_entity.id) not in entity_ids

    def test_get_entity_other_tenant(
        self, authenticated_client, account_factory, entity_factory, db_session
    ):
        """GET /entities/{id} should return 404 for other tenant's entity."""
        other_account = account_factory(name="Other", slug="other")
        other_entity = entity_factory(
            account=other_account,
            name="Other Entity",
        )

        response = authenticated_client.get(f"/api/v1/entities/{other_entity.id}")

        # Should return 404, not 403 (to avoid information leakage)
        assert response.status_code == 404

    def test_update_entity_other_tenant(
        self, authenticated_client, account_factory, entity_factory, db_session
    ):
        """PATCH /entities/{id} should return 404 for other tenant's entity."""
        other_account = account_factory(name="Other", slug="other")
        other_entity = entity_factory(
            account=other_account,
            name="Other Entity",
        )

        response = authenticated_client.patch(
            f"/api/v1/entities/{other_entity.id}",
            json={"name": "Hacked Name"}
        )

        assert response.status_code == 404

        # Verify entity was not modified
        db_session.refresh(other_entity)
        assert other_entity.name == "Other Entity"

    def test_delete_entity_other_tenant(
        self, authenticated_client, account_factory, entity_factory, db_session
    ):
        """DELETE /entities/{id} should return 404 for other tenant's entity."""
        other_account = account_factory(name="Other", slug="other")
        other_entity = entity_factory(
            account=other_account,
            name="Other Entity",
        )

        response = authenticated_client.delete(f"/api/v1/entities/{other_entity.id}")

        assert response.status_code == 404

        # Verify entity still exists
        from app.models import Entity
        entity = db_session.query(Entity).filter(Entity.id == other_entity.id).first()
        assert entity is not None


@pytest.mark.integration
class TestRequirementIsolation:
    """Tests for requirement data isolation."""

    def test_requirement_query_filters_by_account(
        self, authenticated_client, account_factory, requirement_factory, db_session
    ):
        """Requirements should only be visible to their own account."""
        other_account = account_factory(name="Other", slug="other")
        other_req = requirement_factory(account=other_account, name="Other Req")

        my_req = requirement_factory(
            account=authenticated_client.current_account,
            name="My Requirement"
        )

        response = authenticated_client.get("/api/v1/requirements")

        assert response.status_code == 200
        data = response.json()

        req_ids = [r["id"] for r in data.get("items", data)]
        assert str(my_req.id) in req_ids
        assert str(other_req.id) not in req_ids

    def test_get_requirement_other_tenant(
        self, authenticated_client, account_factory, requirement_factory, db_session
    ):
        """GET /requirements/{id} should return 404 for other tenant's requirement."""
        other_account = account_factory(name="Other", slug="other")
        other_req = requirement_factory(account=other_account, name="Other Req")

        response = authenticated_client.get(f"/api/v1/requirements/{other_req.id}")

        assert response.status_code == 404


@pytest.mark.integration
class TestDocumentIsolation:
    """Tests for document data isolation."""

    def test_document_query_filters_by_account(
        self, authenticated_client, account_factory, document_factory, db_session
    ):
        """Documents should only be visible to their own account."""
        other_account = account_factory(name="Other", slug="other")
        other_doc = document_factory(
            account=other_account,
            original_filename="other_doc.pdf"
        )

        my_doc = document_factory(
            account=authenticated_client.current_account,
            original_filename="my_doc.pdf"
        )

        response = authenticated_client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()

        doc_ids = [d["id"] for d in data.get("items", data)]
        assert str(my_doc.id) in doc_ids
        assert str(other_doc.id) not in doc_ids


@pytest.mark.integration
class TestCRMSyncLogIsolation:
    """Tests for CRM sync log data isolation."""

    def test_sync_logs_filters_by_account(
        self, authenticated_client, account_factory, crm_sync_log_factory, db_session
    ):
        """Sync logs should only be visible to their own account."""
        other_account = account_factory(name="Other", slug="other")
        other_log = crm_sync_log_factory(
            account=other_account,
            operation="other-operation"
        )

        my_log = crm_sync_log_factory(
            account=authenticated_client.current_account,
            operation="my-operation"
        )

        response = authenticated_client.get("/api/v1/integrations/sync-logs")

        assert response.status_code == 200
        data = response.json()

        log_ids = [l["id"] for l in data.get("items", [])]
        assert str(my_log.id) in log_ids
        assert str(other_log.id) not in log_ids


@pytest.mark.integration
class TestCreateEntityUsesCurrentAccount:
    """Tests that new entities are created under the current user's account."""

    def test_create_entity_uses_current_account(
        self, authenticated_client, entity_type_factory, db_session
    ):
        """POST /entities should create entity under current user's account."""
        entity_type = entity_type_factory()

        response = authenticated_client.post(
            "/api/v1/entities",
            json={
                "name": "New Entity",
                "entity_type_id": str(entity_type.id),
                "email": "new@example.com",
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Verify entity belongs to current user's account
        from app.models import Entity
        entity = db_session.query(Entity).filter(Entity.id == data["id"]).first()
        assert entity.account_id == authenticated_client.current_account.id


@pytest.mark.integration
class TestWebhookTenantIsolation:
    """Tests for webhook endpoint tenant isolation."""

    def test_zapier_webhook_wrong_account(
        self, client, account_factory, entity_factory, db_session
    ):
        """Zapier webhook should only affect its own account's entities."""
        account_a = account_factory(name="Account A", slug="account-a")
        account_b = account_factory(name="Account B", slug="account-b")

        # Create entity in account A
        entity_a = entity_factory(
            account=account_a,
            name="Entity A",
            email="a@example.com",
            external_id=None,
        )

        # Configure account B with zapier
        account_b.settings = {"crm": {"provider": "zapier", "zapier": {}}}
        db_session.commit()

        # Send webhook to account B with email matching entity in account A
        response = client.post(
            f"/api/v1/integrations/webhooks/zapier/{account_b.id}",
            json={
                "event": "contact.created",
                "external_id": "should-not-link",
                "data": {"email": "a@example.com"},  # Same email as entity A
            }
        )

        assert response.status_code == 200

        # Entity A should NOT have external_id set
        db_session.refresh(entity_a)
        assert entity_a.external_id is None


@pytest.mark.integration
class TestSQLInjection:
    """Tests for SQL injection protection."""

    def test_sql_injection_in_search(self, authenticated_client, entity_factory, db_session):
        """Search parameter should be properly escaped."""
        entity = entity_factory(
            account=authenticated_client.current_account,
            name="Normal Entity",
        )

        # Attempt SQL injection in search
        response = authenticated_client.get(
            "/api/v1/entities",
            params={"search": "'; DROP TABLE entities; --"}
        )

        # Should not error (injection should be escaped)
        assert response.status_code == 200

        # Table should still exist
        from app.models import Entity
        count = db_session.query(Entity).count()
        assert count >= 1

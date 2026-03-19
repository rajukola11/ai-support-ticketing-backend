import pytest


class TestCreateTicket:
    def test_create_ticket_success(self, client, auth_headers):
        response = client.post("/tickets/", json={
            "title": "My printer is broken",
            "description": "The printer stopped working after the last update.",
            "priority": "high",
            "category": "technical"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My printer is broken"
        assert data["status"] == "open"
        assert data["priority"] == "high"
        assert data["category"] == "technical"

    def test_create_ticket_unauthenticated(self, client):
        response = client.post("/tickets/", json={
            "title": "Test ticket",
            "description": "Some description here for testing.",
            "priority": "low",
            "category": "general"
        })
        assert response.status_code == 401

    def test_create_ticket_title_too_short(self, client, auth_headers):
        response = client.post("/tickets/", json={
            "title": "Hi",
            "description": "Some description here for testing.",
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_create_ticket_description_too_short(self, client, auth_headers):
        response = client.post("/tickets/", json={
            "title": "Valid title here",
            "description": "Short",
        }, headers=auth_headers)
        assert response.status_code == 422


class TestListTickets:
    def test_list_tickets_returns_own(self, client, auth_headers, sample_ticket):
        response = client.get("/tickets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(t["id"] == sample_ticket["id"] for t in data)

    def test_list_tickets_unauthenticated(self, client):
        response = client.get("/tickets/")
        assert response.status_code == 401

    def test_list_tickets_filter_by_status(self, client, auth_headers, sample_ticket):
        response = client.get("/tickets/?status=open", headers=auth_headers)
        assert response.status_code == 200
        for ticket in response.json():
            assert ticket["status"] == "open"

    def test_admin_sees_all_tickets(self, client, auth_headers, admin_headers, sample_ticket):
        response = client.get("/tickets/", headers=admin_headers)
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert sample_ticket["id"] in ids


class TestGetTicket:
    def test_get_ticket_success(self, client, auth_headers, sample_ticket):
        response = client.get(f"/tickets/{sample_ticket['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == sample_ticket["id"]
        assert "description" in response.json()

    def test_get_ticket_not_found(self, client, auth_headers):
        response = client.get("/tickets/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == 404

    def test_get_ticket_forbidden_other_user(self, client, sample_ticket, agent_headers, db):
        # Create another regular user
        from app.auth.models import User, UserRole
        from app.auth.security import hash_password
        other = User(
            email="other@example.com",
            hashed_password=hash_password("Other@1234"),
            role=UserRole.USER,
        )
        db.add(other)
        db.commit()
        login = client.post("/auth/login", json={
            "email": "other@example.com", "password": "Other@1234"
        })
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = client.get(f"/tickets/{sample_ticket['id']}", headers=other_headers)
        assert response.status_code == 403


class TestUpdateTicket:
    def test_update_ticket_success(self, client, auth_headers, sample_ticket):
        response = client.patch(f"/tickets/{sample_ticket['id']}", json={
            "title": "Updated ticket title here"
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated ticket title here"

    def test_user_cannot_change_status(self, client, auth_headers, sample_ticket):
        response = client.patch(f"/tickets/{sample_ticket['id']}", json={
            "status": "resolved"
        }, headers=auth_headers)
        assert response.status_code == 200
        # Status should remain open — user cannot change it
        assert response.json()["status"] == "open"

    def test_agent_can_change_status(self, client, agent_headers, sample_ticket):
        response = client.patch(f"/tickets/{sample_ticket['id']}", json={
            "status": "in_progress"
        }, headers=agent_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"


class TestCloseTicket:
    def test_close_ticket_success(self, client, auth_headers, sample_ticket):
        response = client.post(f"/tickets/{sample_ticket['id']}/close", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "closed"

    def test_close_already_closed_ticket(self, client, auth_headers, sample_ticket):
        client.post(f"/tickets/{sample_ticket['id']}/close", headers=auth_headers)
        response = client.post(f"/tickets/{sample_ticket['id']}/close", headers=auth_headers)
        assert response.status_code == 400

    def test_close_not_found(self, client, auth_headers):
        response = client.post("/tickets/00000000-0000-0000-0000-000000000000/close", headers=auth_headers)
        assert response.status_code == 404


class TestDeleteTicket:
    def test_delete_ticket_as_user_forbidden(self, client, auth_headers, sample_ticket):
        response = client.delete(f"/tickets/{sample_ticket['id']}", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_ticket_as_admin(self, client, admin_headers, sample_ticket):
        response = client.delete(f"/tickets/{sample_ticket['id']}", headers=admin_headers)
        assert response.status_code == 204

    def test_delete_ticket_not_found(self, client, admin_headers):
        response = client.delete("/tickets/00000000-0000-0000-0000-000000000000", headers=admin_headers)
        assert response.status_code == 404
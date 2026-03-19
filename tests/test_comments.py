import pytest


class TestAddComment:
    def test_add_comment_success(self, client, auth_headers, sample_ticket):
        response = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "This is a test comment on the ticket.",
            "is_internal": False
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment on the ticket."
        assert data["is_internal"] is False
        assert "author" in data
        assert data["author"]["email"] == "testuser@example.com"

    def test_add_internal_comment_as_user_ignored(self, client, auth_headers, sample_ticket):
        response = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Trying to post internal note as user.",
            "is_internal": True
        }, headers=auth_headers)
        assert response.status_code == 201
        # is_internal should be forced to False for regular users
        assert response.json()["is_internal"] is False

    def test_add_internal_comment_as_agent(self, client, agent_headers, sample_ticket):
        response = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Internal agent note about this ticket.",
            "is_internal": True
        }, headers=agent_headers)
        assert response.status_code == 201
        assert response.json()["is_internal"] is True

    def test_add_comment_unauthenticated(self, client, sample_ticket):
        response = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Unauthenticated comment attempt.",
        })
        assert response.status_code == 401

    def test_add_comment_ticket_not_found(self, client, auth_headers):
        response = client.post("/tickets/00000000-0000-0000-0000-000000000000/comments", json={
            "content": "Comment on nonexistent ticket.",
        }, headers=auth_headers)
        assert response.status_code == 404


class TestListComments:
    def test_list_comments_user_sees_public_only(self, client, auth_headers, agent_headers, sample_ticket):
        # Agent posts internal note
        client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Internal agent note.",
            "is_internal": True
        }, headers=agent_headers)
        # User posts public comment
        client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Public comment from user.",
            "is_internal": False
        }, headers=auth_headers)

        response = client.get(f"/tickets/{sample_ticket['id']}/comments", headers=auth_headers)
        assert response.status_code == 200
        comments = response.json()
        # User should not see internal notes
        assert all(c["is_internal"] is False for c in comments)

    def test_list_comments_agent_sees_internal(self, client, auth_headers, agent_headers, sample_ticket):
        client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Internal note visible to agent.",
            "is_internal": True
        }, headers=agent_headers)

        response = client.get(f"/tickets/{sample_ticket['id']}/comments", headers=agent_headers)
        assert response.status_code == 200
        comments = response.json()
        assert any(c["is_internal"] is True for c in comments)


class TestEditComment:
    def test_edit_comment_success(self, client, auth_headers, sample_ticket):
        post = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Original comment content here.",
        }, headers=auth_headers)
        comment_id = post.json()["id"]

        response = client.patch(
            f"/tickets/{sample_ticket['id']}/comments/{comment_id}",
            json={"content": "Updated comment content here."},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated comment content here."

    def test_edit_comment_wrong_user(self, client, auth_headers, agent_headers, sample_ticket, db):
        post = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Only I can edit this comment.",
        }, headers=auth_headers)
        comment_id = post.json()["id"]

        response = client.patch(
            f"/tickets/{sample_ticket['id']}/comments/{comment_id}",
            json={"content": "Trying to edit someone else comment."},
            headers=agent_headers
        )
        assert response.status_code == 403


class TestDeleteComment:
    def test_delete_comment_by_author(self, client, auth_headers, sample_ticket):
        post = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Comment to be deleted by author.",
        }, headers=auth_headers)
        comment_id = post.json()["id"]

        response = client.delete(
            f"/tickets/{sample_ticket['id']}/comments/{comment_id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    def test_delete_comment_by_admin(self, client, auth_headers, admin_headers, sample_ticket):
        post = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Comment to be deleted by admin.",
        }, headers=auth_headers)
        comment_id = post.json()["id"]

        response = client.delete(
            f"/tickets/{sample_ticket['id']}/comments/{comment_id}",
            headers=admin_headers
        )
        assert response.status_code == 204

    def test_delete_comment_wrong_user(self, client, auth_headers, agent_headers, sample_ticket):
        post = client.post(f"/tickets/{sample_ticket['id']}/comments", json={
            "content": "Only author or admin can delete this.",
        }, headers=auth_headers)
        comment_id = post.json()["id"]

        response = client.delete(
            f"/tickets/{sample_ticket['id']}/comments/{comment_id}",
            headers=agent_headers
        )
        assert response.status_code == 403
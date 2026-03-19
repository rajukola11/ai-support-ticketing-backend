import pytest
from unittest.mock import patch, MagicMock


# -----------------------------
# Mock OpenAI classify response
# -----------------------------
MOCK_CLASSIFY_RESULT = {
    "category": "technical",
    "priority": "high",
    "summary": "User cannot login due to credentials issue.",
    "confidence": 0.95
}

# -----------------------------
# Mock OpenAI draft response
# -----------------------------
MOCK_DRAFT_TEXT = (
    "Dear Customer,\n\n"
    "Thank you for reaching out. We're sorry to hear you're having trouble. "
    "Please try clearing your browser cache and try again.\n\n"
    "Best regards,\nSupport Team"
)


class TestClassifyTicket:
    def test_classify_ticket_success(self, client, auth_headers, sample_ticket):
        with patch("app.ai.services.classify_ticket", return_value=MOCK_CLASSIFY_RESULT):
            response = client.post(
                f"/ai/classify/{sample_ticket['id']}?apply=true",
                headers=auth_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Ticket classified successfully"
        # The latest classify call used our mock so should return technical
        assert data["ai_result"]["suggested_category"] == "technical"
        assert data["ai_result"]["suggested_priority"] == "high"
        assert data["ai_result"]["confidence"] == 0.95
        assert data["ai_result"]["status"] == "success"
        assert data["ticket_updated"] is True

    def test_classify_ticket_not_found(self, client, auth_headers):
        with patch("app.ai.services.classify_ticket", return_value=MOCK_CLASSIFY_RESULT):
            response = client.post(
                "/ai/classify/00000000-0000-0000-0000-000000000000",
                headers=auth_headers
            )
        assert response.status_code == 404

    def test_classify_ticket_unauthenticated(self, client, sample_ticket):
        response = client.post(f"/ai/classify/{sample_ticket['id']}")
        assert response.status_code == 401

    def test_classify_ticket_applies_to_ticket(self, client, auth_headers, sample_ticket):
        with patch("app.ai.services.classify_ticket", return_value=MOCK_CLASSIFY_RESULT):
            client.post(
                f"/ai/classify/{sample_ticket['id']}?apply=true",
                headers=auth_headers
            )
        # Verify ticket was updated with mock values
        ticket = client.get(f"/tickets/{sample_ticket['id']}", headers=auth_headers).json()
        assert ticket["category"] == "technical"
        assert ticket["priority"] == "high"

    def test_classify_without_apply_does_not_update_ticket(self, client, auth_headers, sample_ticket):
        original_category = sample_ticket["category"]
        with patch("app.ai.services.classify_ticket", return_value={
            **MOCK_CLASSIFY_RESULT, "category": "billing"
        }):
            client.post(
                f"/ai/classify/{sample_ticket['id']}?apply=false",
                headers=auth_headers
            )
        ticket = client.get(f"/tickets/{sample_ticket['id']}", headers=auth_headers).json()
        assert ticket["category"] == original_category


class TestGetAIResult:
    def test_get_ai_result_success(self, client, auth_headers, sample_ticket):
        with patch("app.ai.services.classify_ticket", return_value=MOCK_CLASSIFY_RESULT):
            client.post(f"/ai/classify/{sample_ticket['id']}", headers=auth_headers)

        response = client.get(f"/ai/results/{sample_ticket['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == sample_ticket["id"]
        # Latest result should be from our mock call above
        assert data["suggested_category"] == "technical"

    def test_get_ai_result_no_classify_still_has_result(self, client, auth_headers, sample_ticket):
        # sample_ticket auto-classifies on creation so there's always at least one result
        response = client.get(f"/ai/results/{sample_ticket['id']}", headers=auth_headers)
        assert response.status_code == 200

    def test_get_ai_result_ticket_not_found(self, client, auth_headers):
        response = client.get("/ai/results/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == 404

    def test_get_ai_result_history(self, client, auth_headers, sample_ticket):
        with patch("app.ai.services.classify_ticket", return_value=MOCK_CLASSIFY_RESULT):
            client.post(f"/ai/classify/{sample_ticket['id']}", headers=auth_headers)
            client.post(f"/ai/classify/{sample_ticket['id']}", headers=auth_headers)

        response = client.get(f"/ai/results/{sample_ticket['id']}/history", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 2


class TestDraftResponse:
    def test_draft_requires_agent_role(self, client, auth_headers, sample_ticket):
        with patch("app.ai.services.generate_draft_response", return_value=MOCK_DRAFT_TEXT):
            response = client.post(
                f"/ai/draft/{sample_ticket['id']}",
                headers=auth_headers
            )
        assert response.status_code == 403

    def test_draft_success_as_agent(self, client, agent_headers, sample_ticket):
        with patch("app.ai.services.generate_draft_response", return_value=MOCK_DRAFT_TEXT):
            response = client.post(
                f"/ai/draft/{sample_ticket['id']}",
                headers=agent_headers
            )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Draft response generated successfully"
        assert len(data["draft_response"]) > 50
        assert data["model_used"] is not None

    def test_draft_ticket_not_found(self, client, agent_headers):
        with patch("app.ai.services.generate_draft_response", return_value=MOCK_DRAFT_TEXT):
            response = client.post(
                "/ai/draft/00000000-0000-0000-0000-000000000000",
                headers=agent_headers
            )
        assert response.status_code == 404

    def test_draft_unauthenticated(self, client, sample_ticket):
        response = client.post(f"/ai/draft/{sample_ticket['id']}")
        assert response.status_code == 401
import logging
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.ai.models import AIResult, AIResultStatus
from app.ai.classifier import classify_ticket
from app.ai.draft import generate_draft_response
from app.tickets.models import Ticket, TicketCategory, TicketPriority
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# -----------------------------
# Run classification & store result
# -----------------------------
def run_classification(db: Session, ticket: Ticket, apply: bool = True) -> AIResult:
    ai_result = AIResult(
        ticket_id=ticket.id,
        model_used=settings.OPENAI_MODEL,
    )

    try:
        result = classify_ticket(ticket.title, ticket.description)

        ai_result.suggested_category = result["category"]
        ai_result.suggested_priority = result["priority"]
        ai_result.summary = result["summary"]
        ai_result.confidence = result["confidence"]
        ai_result.status = AIResultStatus.SUCCESS

        if apply:
            _apply_to_ticket(db, ticket, result)
            ai_result.applied = True

    except Exception as e:
        logger.error(f"Classification failed for ticket {ticket.id}: {e}")
        ai_result.status = AIResultStatus.FAILED
        ai_result.error_message = str(e)

    db.add(ai_result)
    db.commit()
    db.refresh(ai_result)
    return ai_result


def _apply_to_ticket(db: Session, ticket: Ticket, result: dict) -> None:
    category_map = {
        "general": TicketCategory.GENERAL,
        "billing": TicketCategory.BILLING,
        "technical": TicketCategory.TECHNICAL,
        "other": TicketCategory.OTHER,
    }
    priority_map = {
        "low": TicketPriority.LOW,
        "medium": TicketPriority.MEDIUM,
        "high": TicketPriority.HIGH,
        "critical": TicketPriority.CRITICAL,
    }

    if result.get("category") in category_map:
        ticket.category = category_map[result["category"]]
    if result.get("priority") in priority_map:
        ticket.priority = priority_map[result["priority"]]

    db.commit()


# -----------------------------
# Generate draft response
# -----------------------------
def run_draft_generation(db: Session, ticket: Ticket) -> AIResult:
    """
    Generates a draft reply for the ticket using comment history as context.
    Stores result in ai_results table.
    """
    ai_result = AIResult(
        ticket_id=ticket.id,
        model_used=settings.OPENAI_MODEL,
    )

    try:
        # Fetch public comments for context
        from app.comments.models import Comment
        comments = (
            db.query(Comment)
            .filter(Comment.ticket_id == ticket.id, Comment.is_internal == False)
            .order_by(Comment.created_at.asc())
            .all()
        )

        comments_data = [
            {"content": c.content, "is_internal": c.is_internal}
            for c in comments
        ]

        draft = generate_draft_response(
            title=ticket.title,
            description=ticket.description,
            category=ticket.category.value,
            priority=ticket.priority.value,
            comments=comments_data,
        )

        ai_result.draft_response = draft
        ai_result.status = AIResultStatus.SUCCESS

    except Exception as e:
        logger.error(f"Draft generation failed for ticket {ticket.id}: {e}")
        ai_result.status = AIResultStatus.FAILED
        ai_result.error_message = str(e)

    db.add(ai_result)
    db.commit()
    db.refresh(ai_result)
    return ai_result


# -----------------------------
# Get latest AI result for ticket
# -----------------------------
def get_latest_result(db: Session, ticket_id: UUID) -> Optional[AIResult]:
    return (
        db.query(AIResult)
        .filter(AIResult.ticket_id == ticket_id)
        .order_by(AIResult.created_at.desc())
        .first()
    )


# -----------------------------
# Get all AI results for ticket
# -----------------------------
def get_all_results(db: Session, ticket_id: UUID) -> list[AIResult]:
    return (
        db.query(AIResult)
        .filter(AIResult.ticket_id == ticket_id)
        .order_by(AIResult.created_at.desc())
        .all()
    )
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.auth.security import get_current_user
from app.auth.models import User, UserRole
from app.tickets.services import get_ticket_by_id
from app.ai import services, schemas

router = APIRouter(prefix="/ai", tags=["AI"])


def is_support_or_admin(user: User) -> bool:
    return user.role in (UserRole.SUPPORT_AGENT, UserRole.ADMIN)


# -----------------------------
# Manually trigger classification
# -----------------------------
@router.post("/classify/{ticket_id}", response_model=schemas.AIClassifyResponse)
def classify_ticket(
    ticket_id: UUID,
    apply: bool = Query(True, description="Apply AI suggestions to ticket fields"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Only owner, support agents, or admins can trigger classification
    if not is_support_or_admin(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    ai_result = services.run_classification(db, ticket, apply=apply)

    if ai_result.status.value == "failed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI classification failed: {ai_result.error_message}"
        )

    return schemas.AIClassifyResponse(
        message="Ticket classified successfully",
        ai_result=ai_result,
        ticket_updated=apply,
    )


# -----------------------------
# Get latest AI result for a ticket
# -----------------------------
@router.get("/results/{ticket_id}", response_model=schemas.AIResultResponse)
def get_ai_result(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if not is_support_or_admin(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = services.get_latest_result(db, ticket_id)

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No AI results found for this ticket")

    return result


# -----------------------------
# Get all AI results for a ticket
# -----------------------------
@router.get("/results/{ticket_id}/history", response_model=list[schemas.AIResultResponse])
def get_ai_result_history(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = get_ticket_by_id(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if not is_support_or_admin(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return services.get_all_results(db, ticket_id)
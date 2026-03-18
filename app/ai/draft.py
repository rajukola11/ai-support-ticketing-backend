import logging
from app.ai.client import get_openai_client
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a professional customer support agent for a software company.
Your job is to write a helpful, empathetic, and clear reply to a customer support ticket.

Guidelines:
- Be polite and empathetic
- Be concise but thorough
- Offer concrete next steps or solutions
- Sign off as "Support Team"
- Do NOT make up information you don't have
- If you cannot solve the issue directly, acknowledge it and tell the customer what will happen next

Respond with ONLY the draft reply text — no subject line, no metadata, no extra explanation.
"""


def generate_draft_response(
    title: str,
    description: str,
    category: str,
    priority: str,
    comments: list[dict] = [],
) -> str:
    """
    Generates a draft support reply based on the ticket details and comment history.
    Returns the draft as a plain string.
    """
    client = get_openai_client()

    # Build context from comments if any
    comment_context = ""
    if comments:
        comment_context = "\n\nPrevious conversation:\n"
        for c in comments:
            role = "Customer" if c.get("is_internal") is False else "Agent (internal)"
            comment_context += f"{role}: {c.get('content')}\n"

    user_message = (
        f"Ticket Title: {title}\n"
        f"Category: {category}\n"
        f"Priority: {priority}\n\n"
        f"Customer Message:\n{description}"
        f"{comment_context}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,  # Higher temp for more natural-sounding replies
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Draft generation failed: {e}")
        raise
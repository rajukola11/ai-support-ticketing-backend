import json
import logging
from app.ai.client import get_openai_client
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an AI assistant for a customer support ticketing system.
Your job is to analyze support tickets and return a JSON classification.

You must respond ONLY with a valid JSON object — no explanation, no markdown, no extra text.

JSON format:
{
  "category": "general" | "billing" | "technical" | "other",
  "priority": "low" | "medium" | "high" | "critical",
  "summary": "One sentence summary of the issue (max 150 chars)",
  "confidence": 0.0 to 1.0
}

Classification rules:
- category "billing": payment issues, refunds, subscriptions, invoices
- category "technical": bugs, errors, login issues, performance problems
- category "general": questions, feedback, feature requests
- category "other": anything that doesn't fit above

- priority "critical": system down, security breach, data loss, cannot access account
- priority "high": major feature broken, significant impact on user
- priority "medium": partial functionality issue, workaround exists
- priority "low": minor issue, cosmetic bug, general question
"""


def classify_ticket(title: str, description: str) -> dict:
    """
    Sends ticket to OpenAI for classification.
    Returns dict with category, priority, summary, confidence.
    """
    client = get_openai_client()

    user_message = f"Title: {title}\n\nDescription: {description}"

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,  # Low temp for consistent classification
            max_tokens=200,
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        # Validate expected keys are present
        required_keys = {"category", "priority", "summary", "confidence"}
        if not required_keys.issubset(result.keys()):
            raise ValueError(f"Missing keys in AI response: {result}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"AI classification failed: {e}")
        raise
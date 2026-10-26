
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your project's .env file."
    )


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=3,
            initial_delay=2.0,
            max_delay=8.0,
            http_status_codes=[408, 429, 500, 502, 503, 504],
        )
    ),
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

router = APIRouter(prefix="/chat", tags=["AgriAssist"])


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    state: str | None = None
    district: str | None = None
    season: str | None = None
    crop: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    reply: str
    source: str


SYSTEM_INSTRUCTIONS = """
You are AgriSense, a conversational agricultural AI assistant.

Your responsibilities:
- Answer general agricultural questions in clear, helpful language.
- Understand natural wording, spelling variations, and follow-up questions.
- Explain soil nutrients, crop recommendations, seasons, irrigation,
  fertilizer, crop diseases, and agricultural concepts.
- Use supplied historical dataset context when answering questions about
  recorded crop production.
- Never invent historical production numbers or claim that you queried
  the dataset when no dataset results were provided.
- Historical production is not a forecast of future production, crop
  suitability, or profitability.
- Do not invent local weather, soil measurements, market prices, or
  agricultural statistics.
- Give cautious general guidance for pesticide and disease questions.
  Recommend a local agricultural expert for diagnosis or precise dosage.
- If important details are missing, ask a short clarifying question.
- Do not claim to have performed actions you did not perform.
"""


def get_historical_context(request: ChatRequest) -> str | None:
    """Retrieve verified historical records when the question needs them."""

    message = request.message.casefold()

    historical_terms = [
        "historical",
        "history",
        "production",
        "produced",
        "grown most",
        "top crops",
        "ranking",
        "trend",
        "over the years",
        "yearly",
        "by year",
        "previous year",
        "past years",
    ]

    if not any(term in message for term in historical_terms):
        return None

    if not request.state or not request.district or not request.season:
        return (
            "The user has not supplied all required location details for a "
            "historical lookup. Ask for state, district, and season before "
            "making claims about district-level historical production."
        )

    try:
        if request.crop and any(
            term in message
            for term in [
                "trend",
                "over the years",
                "yearly",
                "by year",
                "previous year",
                "past years",
            ]
        ):
            result = get_crop_production_trend(
                state=request.state,
                district=request.district,
                crop=request.crop,
                season=request.season,
            )

            trend = result.get("trend", [])

            if not trend:
                return "No matching historical production trend was found."

            records = "\n".join(
                f"Year: {item['year']}; "
                f"recorded production: {item['total_production']:,.2f}"
                for item in trend
            )

            return (
                f"Historical production trend for {request.crop}, "
                f"{request.district}, {request.state}, season "
                f"{request.season}:\n{records}\n"
                "These are historical records, not future predictions. "
                "The production unit has not been verified."
            )

        result = get_district_crop_ranking(
            state=request.state,
            district=request.district,
            season=request.season,
            limit=5,
        )

        crops = result.get("crops", [])

        if not crops:
            return result.get(
                "message",
                "No matching historical crop records were found.",
            )

        records = "\n".join(
            f"Crop: {item['Crop']}; "
            f"recorded production total: "
            f"{item['total_production']:,.2f}; "
            f"recorded area total: {item.get('total_area', 0):,.2f}"
            for item in crops
        )

        return (
            f"Historical crop records for {request.district}, "
            f"{request.state}, season {request.season}, covering "
            f"1997–2014:\n{records}\n"
            "Production units have not been verified. These historical "
            "totals do not establish future suitability or profitability."
        )

    except (ValueError, FileNotFoundError) as exc:
        return (
            "Historical data lookup was unsuccessful. The location or crop "
            f"may not match the dataset. Technical detail: {str(exc)}"
        )


def generate_reply(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()

    if not message:
        return ChatResponse(
            reply="Please enter an agricultural question.",
            source="fallback",
        )

    context = get_historical_context(request)

    prompt_parts = [SYSTEM_INSTRUCTIONS]

    if context:
        prompt_parts.append(
            "Historical dataset lookup result or lookup limitation:\n"
            + context
        )

    # Keep only the latest messages to provide conversational context.
    for item in request.history[-10:]:
        if item.role not in {"user", "assistant"}:
            continue

        prompt_parts.append(
            f"{item.role.upper()}: {item.content}"
        )

    prompt_parts.append(f"USER: {message}")
    prompt_parts.append("ASSISTANT:")

    try:
        response = gemini_client.interactions.create(
        model=GEMINI_MODEL,
        input="\n\n".join(prompt_parts),
        )

        reply = (response.output_text or "").strip()

        if not reply:
            raise RuntimeError("Gemini returned an empty response.")

        source = (
            "gemini_with_historical_data"
            if context
            else "gemini"
        )

        return ChatResponse(reply=reply, source=source)

    except Exception as exc:
        # Log details only on the backend; do not expose keys or raw errors.
        print(
    f"AgriAssist Gemini request failed: "
    f"{type(exc).__name__}: {str(exc)[:500]}"
)

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI assistant could not generate a response. "
                "Check the backend logs and Gemini API configuration."
            ),
        ) from exc


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    return generate_reply(request)


import os
import logging
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from historical_insights import (
    get_district_crop_ranking,
    get_crop_production_trend,
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your project's .env file."
    )

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

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

router = APIRouter(prefix="/chat", tags=["AgriAssist"])


# --------------------------------------------------
# Request and Response Models
# --------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    state: str | None = None
    district: str | None = None
    season: str | None = None
    crop: str | None = None
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )


class ChatResponse(BaseModel):
    reply: str
    source: str


# --------------------------------------------------
# Agricultural Assistant Instructions
# --------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are AgriSmart AgriAssist, a helpful agricultural AI assistant.

Your responsibilities:

1. Answer agricultural questions in clear, simple language.
2. Understand spelling variations, informal wording, and follow-up questions.
3. Explain soil nutrients, crop suitability, seasons, irrigation,
   fertilizer management, crop diseases, and agricultural concepts.
4. Provide practical suggestions that farmers can understand and apply.
5. Use supplied historical dataset context when answering questions
   about recorded crop production.
6. Never invent historical production numbers or claim that you queried
   a dataset when no dataset results were provided.
7. Historical production is not a prediction of future production,
   crop suitability, or profitability.
8. Do not invent local weather, soil measurements, market prices,
   or agricultural statistics.
9. Do not promise a specific percentage increase in crop production
   without reliable supporting evidence.
10. Explain the difference between model-based crop suitability
    and actual farm production.
11. For fertilizer and pesticide questions, provide cautious general
    guidance and recommend local agricultural experts for diagnosis
    or precise dosage.
12. If important information is missing, ask a short clarifying question.
13. Do not claim to have performed actions you did not perform.

When discussing crop recommendations:
- Explain why the crop may be suitable.
- Identify relevant soil and climate factors.
- Suggest practical ways to manage limiting factors.
- Clearly communicate uncertainty.
- Do not guarantee yield or profitability.
"""


# --------------------------------------------------
# Historical Data Context
# --------------------------------------------------

HISTORICAL_TERMS = [
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

TREND_TERMS = [
    "trend",
    "over the years",
    "yearly",
    "by year",
    "previous year",
    "past years",
]


def get_historical_context(
    request: ChatRequest,
) -> tuple[str | None, str]:
    """
    Retrieve historical production context when relevant.

    Returns:
        context: Historical records or an explanation of lookup limitations.
        status: retrieved, missing_details, no_records, error, or not_requested.
    """

    message = request.message.casefold()

    historical_requested = any(
        term in message for term in HISTORICAL_TERMS
    )

    if not historical_requested:
        return None, "not_requested"

    # Require location and season for historical lookup.
    if not all(
        [
            request.state,
            request.district,
            request.season,
        ]
    ):
        return (
            "The user has not supplied all required location details "
            "for a historical lookup. Ask for state, district, and "
            "season before making claims about district-level "
            "historical production.",
            "missing_details",
        )

    try:
        # Crop-specific production trend.
        if request.crop and any(
            term in message for term in TREND_TERMS
        ):
            result = get_crop_production_trend(
                state=request.state,
                district=request.district,
                crop=request.crop,
                season=request.season,
            )

            trend = result.get("trend", [])

            if not trend:
                return (
                    "No matching historical production trend was found "
                    "for the supplied crop and location.",
                    "no_records",
                )

            records = "\n".join(
                (
                    f"Year: {item['year']}; "
                    f"recorded production: "
                    f"{item['total_production']:,.2f}"
                )
                for item in trend
            )

            context = (
                f"Historical production trend for {request.crop}, "
                f"{request.district}, {request.state}, "
                f"season {request.season}:\n"
                f"{records}\n"
                "These are historical records, not future predictions. "
                "The production unit has not been verified."
            )

            return context, "retrieved"

        # District-level crop ranking.
        result = get_district_crop_ranking(
            state=request.state,
            district=request.district,
            season=request.season,
            limit=5,
        )

        crops = result.get("crops", [])

        if not crops:
            return (
                result.get(
                    "message",
                    "No matching historical crop records were found.",
                ),
                "no_records",
            )

        records = "\n".join(
            (
                f"Crop: {item['Crop']}; "
                f"recorded production total: "
                f"{item['total_production']:,.2f}; "
                f"recorded area total: "
                f"{item.get('total_area', 0):,.2f}"
            )
            for item in crops
        )

        context = (
            f"Historical crop records for {request.district}, "
            f"{request.state}, season {request.season}, "
            f"covering 1997–2014:\n"
            f"{records}\n"
            "Production units have not been verified. These historical "
            "totals do not establish future suitability or profitability."
        )

        return context, "retrieved"

    except (ValueError, FileNotFoundError) as exc:
        logger.warning(
            "Historical data lookup failed: %s",
            type(exc).__name__,
        )

        return (
            "The historical data lookup was unsuccessful. "
            "The location, crop, or season may not match the dataset.",
            "error",
        )

    except Exception:
        logger.exception("Unexpected historical lookup error")

        return (
            "The historical data service is temporarily unavailable. "
            "Do not invent historical production figures.",
            "error",
        )


# --------------------------------------------------
# Gemini Response Generation
# --------------------------------------------------

def generate_reply(request: ChatRequest) -> ChatResponse:

    message = request.message.strip()

    if not message:
        return ChatResponse(
            reply="Please enter an agricultural question.",
            source="fallback",
        )

    context, historical_status = get_historical_context(request)

    prompt_parts = [
        SYSTEM_INSTRUCTIONS,
    ]

    if context:
        prompt_parts.append(
            "Historical dataset lookup result or limitation:\n"
            + context
        )

    # Include recent conversation history.
    for item in request.history[-10:]:

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
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Identify the actual context used.
        if historical_status == "retrieved":
            source = "gemini_with_historical_data"

        elif historical_status == "missing_details":
            source = "gemini_historical_details_required"

        elif historical_status == "no_records":
            source = "gemini_historical_data_not_found"

        elif historical_status == "error":
            source = "gemini_historical_lookup_failed"

        else:
            source = "gemini"

        return ChatResponse(
            reply=reply,
            source=source,
        )

    except Exception as exc:

        status_code = getattr(exc, "code", None)
        error_message = str(exc)

        logger.exception(
            "AgriAssist Gemini request failed. "
            "Status: %s | Error: %s",
            status_code,
            error_message[:500],
        )

        if status_code == 503:
            raise HTTPException(
                status_code=503,
                detail="Gemini is temporarily unavailable. Please try again shortly."
            ) from exc

        elif status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini request limit reached. Please try again later."
            ) from exc

        elif status_code == 504:
            raise HTTPException(
                status_code=504,
                detail="Gemini response timed out. Please try again."
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="The AI Assistant could not generate a response."
        ) from exc


# --------------------------------------------------
# API Endpoint
# --------------------------------------------------

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    return generate_reply(request)

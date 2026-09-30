from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
import json
import tempfile

import cv2
import numpy as np


# ============================================================
# Environment
# ============================================================

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")


# ============================================================
# MongoDB
# ============================================================

mongo_url = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(mongo_url) if mongo_url else None
db = client[os.getenv("DB_NAME", "fake_news_db")] if client else None


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(title="Fake News Detection API")

api_router = APIRouter(prefix="/api")


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# API Keys
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


# ============================================================
# Constants
# ============================================================

OPENAI_MODEL = "gpt-5.6-luna"
DEMO_MODE = True

SUPPORTED_LANGUAGES = [
    "english",
    "hindi",
    "marathi",
    "tamil",
    "hinglish"
]


# ============================================================
# Pydantic Models
# ============================================================

class TextDetectionRequest(BaseModel):
    text: str = Field(..., description="News text to analyze")


class DetectionResult(BaseModel):
    status: str
    confidence: float
    explanation: str
    explanation_english: Optional[str] = None
    suspicious_keywords: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    timestamp: str
    detected_language: Optional[str] = None


class VerificationRequest(BaseModel):
    claim: str = Field(..., description="Claim to verify")


class NewsApiKeyRequest(BaseModel):
    api_key: str = Field(..., description="News API key to configure")


class HistoryDeleteRequest(BaseModel):
    ids: Optional[List[str]] = None


# ============================================================
# Helper Functions
# ============================================================

def parse_llm_json(response_text: str) -> dict:
    """
    Parse JSON returned by the LLM.

    Handles both plain JSON and markdown code blocks.
    """
    if not response_text:
        raise ValueError("Empty response received from OpenAI")

    text = response_text.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()

    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    return json.loads(text)


def get_image_mime_type(content_type: Optional[str]) -> str:
    """
    Convert uploaded file MIME type into a format accepted by OpenAI.
    """
    allowed_types = {
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif"
    }

    return allowed_types.get(content_type, "image/jpeg")

# Local history used when DEMO_MODE is enabled.
demo_history = []


async def save_to_history(
    analysis_type: str,
    content_preview: str,
    result: dict,
    filename: str = None
):
    """Save analysis result to MongoDB or local demo memory."""

    doc = {
        "id": str(uuid.uuid4()),
        "type": analysis_type,
        "content_preview": content_preview[:300],
        "filename": filename,
        "status": result.get("status", "UNKNOWN"),
        "confidence": result.get("confidence", 0),
        "explanation": result.get("explanation", ""),
        "suspicious_keywords": result.get(
            "suspicious_keywords", []
        ),
        "sources": result.get("sources", []),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if DEMO_MODE:
        demo_history.insert(0, doc)

        # Keep only the latest 100 demo records.
        del demo_history[100:]

        return doc["id"]

    await db.analysis_history.insert_one(doc)

    return doc["id"]


# ============================================================
# OpenAI - Text Analysis
# ============================================================

async def analyze_text_with_llm(text: str) -> dict:
    """Analyze news text using OpenAI or local demo mode."""

    if DEMO_MODE:
        lower_text = text.lower()

        suspicious_words = [
            word for word in [
                "breaking",
                "shocking",
                "secret",
                "guaranteed",
                "miracle",
                "100%",
                "government has announced",
                "from tomorrow",
                "immediately",
                "viral"
            ]
            if word in lower_text
        ]

        if suspicious_words:
            status = "FAKE"
            confidence = 72
            explanation = (
                "DEMO MODE: The text contains sensational or highly definitive "
                "language. These indicators alone do not prove that the claim is false."
            )
        else:
            status = "REAL"
            confidence = 55
            explanation = (
                "DEMO MODE: No strong sensational-language indicators were detected. "
                "This does not prove that the news is authentic."
            )

        return {
            "status": status,
            "confidence": confidence,
            "detected_language": "english",
            "explanation": explanation,
            "explanation_english": explanation,
            "suspicious_keywords": suspicious_words,
            "credibility_indicators": [
                "Local demo analysis",
                "No live external verification performed"
            ],
            "mode": "DEMO"
        }

    try:
        response = await openai_client.responses.create(
            model=OPENAI_MODEL,

            instructions="""
You are an AI-assisted news analysis system.

You support:
- English
- Hindi
- Marathi
- Tamil
- Hinglish

Analyze the supplied news text.

Return ONLY valid JSON.

Rules:
1. Detect the language of the input.
2. Provide the main explanation in the same language as the input.
3. Also provide an English explanation.
4. Do not invent sources or facts.
5. Treat the result as an AI-assisted assessment, not definitive proof of truth.
6. If there is insufficient information, clearly explain the limitation.
7. Do not claim certainty that cannot be supported by the provided text.

Required JSON format:

{
    "status": "REAL" or "FAKE",
    "confidence": number between 0 and 100,
    "detected_language": "english" or "hindi" or "marathi" or "tamil" or "hinglish",
    "explanation": "detailed explanation in the input language",
    "explanation_english": "detailed explanation in English",
    "suspicious_keywords": ["keyword1", "keyword2"],
    "credibility_indicators": ["indicator1", "indicator2"]
}
""",

            input=f"Analyze this news text and return the result as JSON:\n\n{text}",

            text={
                "format": {
                    "type": "json_object"
                }
            },

            max_output_tokens=1200
        )

        return parse_llm_json(response.output_text)

    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Text analysis failed: {str(e)}"
        )

# ============================================================
# OpenAI - Image Analysis
# ============================================================

async def analyze_image_with_vision(
    image_base64: str,
    mime_type: str = "image/jpeg"
) -> dict:
    """
    Analyze an image for possible manipulation,
    deepfake or AI-generation indicators.
    """

    if DEMO_MODE:
        return {
            "status": "UNVERIFIED",
            "confidence": 50,
            "explanation": (
                "DEMO MODE: Image analysis is running without a live AI vision model. "
                "No reliable determination of authenticity can be made locally."
            ),
            "manipulation_indicators": [],
            "authenticity_indicators": [
                "Local demo mode",
                "Live AI vision analysis disabled"
            ],
            "mode": "DEMO"
        }

    try:
        image_url = f"data:{mime_type};base64,{image_base64}"

        response = await openai_client.responses.create(
            model=OPENAI_MODEL,

            instructions="""
You are an AI-assisted image analysis system.

Analyze the supplied image for visual indicators that may suggest:

- AI generation
- image manipulation
- deepfake-like artifacts
- inconsistent lighting
- distorted anatomy
- unnatural facial features
- inconsistent shadows
- unusual edges
- compositing artifacts
- inconsistent image quality

Important:
1. Do not claim that an image is definitively real or fake solely from visual inspection.
2. Explain the actual visual indicators you observe.
3. If evidence is weak or inconclusive, say so.
4. Return ONLY valid JSON.

Required JSON format:

{
    "status": "REAL" or "FAKE",
    "confidence": number between 0 and 100,
    "explanation": "detailed explanation",
    "manipulation_indicators": ["indicator1", "indicator2"],
    "authenticity_indicators": ["indicator1", "indicator2"]
}
""",

            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": ("Analyze this image for possible manipulation, deepfake, or AI-generation indicators and return the result as JSON.")
                        },
                        {
                            "type": "input_image",
                            "image_url": image_url,
                            "detail": "high"
                        }
                    ]
                }
            ],

            text={
                "format": {
                    "type": "json_object"
                }
            },

            max_output_tokens=1000
        )

        return parse_llm_json(response.output_text)

    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


# ============================================================
# OpenAI - Claim Verification
# ============================================================

async def verify_claim_with_llm(claim: str) -> dict:
    """Analyze a claim using OpenAI or local demo mode."""

    if DEMO_MODE:
        return {
            "status": "UNVERIFIED",
            "confidence": 50,
            "detected_language": "english",
            "explanation": (
                "DEMO MODE: This claim has not been verified using live "
                "external sources or an AI model."
            ),
            "explanation_english": (
                "DEMO MODE: This claim has not been verified using live "
                "external sources or an AI model."
            ),
            "supporting_facts": [],
            "related_context": (
                "Enable live AI/API verification when an API service is available."
            ),
            "mode": "DEMO"
        }

    try:
        response = await openai_client.responses.create(
            model=OPENAI_MODEL,

            instructions="""
You are an AI-assisted claim verification system.

You support:
- English
- Hindi
- Marathi
- Tamil
- Hinglish

Analyze the claim using known information and logical consistency.

Important:
1. Detect the language of the input claim.
2. Provide the main explanation in the same language.
3. Always provide an English explanation.
4. Do not fabricate evidence.
5. Do not pretend that general model knowledge is real-time verification.
6. If the claim requires current information, clearly state that external verification is needed.
7. This is an AI-assisted assessment, not definitive proof.
8. Return ONLY valid JSON.

Required JSON format:

{
    "status": "VERIFIED" or "UNVERIFIED" or "PARTIALLY_VERIFIED",
    "confidence": number between 0 and 100,
    "detected_language": "english" or "hindi" or "marathi" or "tamil" or "hinglish",
    "explanation": "detailed explanation in the input language",
    "explanation_english": "detailed explanation in English",
    "supporting_facts": ["fact1", "fact2"],
    "related_context": "relevant context or limitations"
}
""",

            input=f"Analyze this claim and return the result as JSON:\n\n{claim}",

            text={
                "format": {
                    "type": "json_object"
                }
            },

            max_output_tokens=1200
        )

        return parse_llm_json(response.output_text)

    except Exception as e:
        logger.error(f"Error in claim verification: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )


# ============================================================
# News API Verification
# ============================================================

async def verify_with_news_api(claim: str) -> Optional[dict]:
    """Verify a claim using News API for real-time news comparison."""

    import requests

    if not NEWS_API_KEY:
        return None

    try:
        search_query = claim[:100]

        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": search_query,
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 10
            },
            timeout=10
        )

        if response.status_code != 200:
            logger.warning(
                f"News API returned status {response.status_code}"
            )
            return None

        data = response.json()

        if data.get("status") != "ok" or not data.get("articles"):
            return None

        articles = data["articles"]

        matching_articles = []

        for article in articles[:5]:
            matching_articles.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get(
                    "name",
                    "Unknown"
                ),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "description": article.get("description", "")
            })

        return {
            "articles_found": len(articles),
            "matching_articles": matching_articles,
            "sources": list(
                set(
                    article.get("source", {}).get("name", "")
                    for article in articles[:5]
                )
            )
        }

    except Exception as e:
        logger.error(f"News API error: {str(e)}")
        return None


# ============================================================
# Routes - Basic
# ============================================================

@api_router.get("/")
async def root():
    return {
        "message": "Fake News Detection API",
        "status": "operational"
    }


# ============================================================
# Routes - Text Detection
# ============================================================

@api_router.post("/detect-text")
async def detect_text(request: TextDetectionRequest):
    """Detect fake news in text using AI."""

    try:
        logger.info(
            f"Analyzing text: {request.text[:100]}..."
        )

        result = await analyze_text_with_llm(request.text)

        response_data = {
            "status": result.get("status", "UNKNOWN"),
            "confidence": float(
                result.get("confidence", 50)
            ),
            "explanation": result.get(
                "explanation",
                "Analysis completed"
            ),
            "explanation_english": result.get(
                "explanation_english",
                result.get("explanation", "")
            ),
            "detected_language": result.get(
                "detected_language",
                "english"
            ),
            "suspicious_keywords": result.get(
                "suspicious_keywords",
                []
            ),
            "sources": result.get(
                "credibility_indicators",
                []
            ),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

        await save_to_history(
            "text",
            request.text,
            response_data
        )

        return response_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Text detection error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# Routes - Image Detection
# ============================================================

@api_router.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
    """Detect manipulation/deepfakes in images."""

    try:
        logger.info(
            f"Analyzing image: {file.filename}"
        )

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Empty image file uploaded"
            )

        image_base64 = base64.b64encode(
            contents
        ).decode("utf-8")

        mime_type = get_image_mime_type(
            file.content_type
        )

        result = await analyze_image_with_vision(
            image_base64,
            mime_type
        )

        response_data = {
            "status": result.get(
                "status",
                "UNKNOWN"
            ),
            "confidence": float(
                result.get(
                    "confidence",
                    50
                )
            ),
            "explanation": result.get(
                "explanation",
                "Analysis completed"
            ),
            "suspicious_keywords": result.get(
                "manipulation_indicators",
                []
            ),
            "sources": result.get(
                "authenticity_indicators",
                []
            ),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

        await save_to_history(
            "image",
            f"Image: {file.filename}",
            response_data,
            filename=file.filename
        )

        return response_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Image detection error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# Routes - Video Detection
# ============================================================

@api_router.post("/detect-video")
async def detect_video(file: UploadFile = File(...)):
    """Detect deepfakes in videos using sampled frames."""

    temp_path = None

    try:
        logger.info(
            f"Analyzing video: {file.filename}"
        )

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid file: No filename provided"
            )

        valid_extensions = [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm"
        ]

        file_ext = os.path.splitext(
            file.filename.lower()
        )[1]

        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported video format. "
                    "Please upload one of: "
                    + ", ".join(valid_extensions)
                )
            )

        contents = await file.read()

        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )

        max_size = 100 * 1024 * 1024

        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Video file too large. "
                    "Maximum size is 100MB"
                )
            )

        # Windows-compatible temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(contents)

        cap = cv2.VideoCapture(temp_path)

        if not cap.isOpened():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unable to open video file. "
                    "Please ensure it is a valid video format."
                )
            )

        frames_to_analyze = []

        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        frame_count = 0

        if total_frames <= 0:

            max_frames = 5

            while len(frames_to_analyze) < max_frames:

                ret, frame = cap.read()

                if not ret:
                    break

                success, buffer = cv2.imencode(
                    ".jpg",
                    frame
                )

                if success:
                    frame_base64 = base64.b64encode(
                        buffer
                    ).decode("utf-8")

                    frames_to_analyze.append(
                        frame_base64
                    )

        else:

            sample_indices = np.linspace(
                0,
                total_frames - 1,
                min(5, total_frames),
                dtype=int
            )

            sample_indices = set(
                sample_indices.tolist()
            )

            while cap.isOpened():

                ret, frame = cap.read()

                if not ret:
                    break

                if frame_count in sample_indices:

                    success, buffer = cv2.imencode(
                        ".jpg",
                        frame
                    )

                    if success:
                        frame_base64 = base64.b64encode(
                            buffer
                        ).decode("utf-8")

                        frames_to_analyze.append(
                            frame_base64
                        )

                frame_count += 1

        cap.release()

        if not frames_to_analyze:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No frames could be extracted "
                    "from the video."
                )
            )

        result = await analyze_image_with_vision(
            frames_to_analyze[0],
            "image/jpeg"
        )

        response_data = {
            "status": result.get(
                "status",
                "UNKNOWN"
            ),
            "confidence": float(
                result.get(
                    "confidence",
                    50
                )
            ),
            "explanation": (
                result.get(
                    "explanation",
                    "Video analysis completed"
                )
                + f" (Analyzed {len(frames_to_analyze)} frames)"
            ),
            "suspicious_keywords": result.get(
                "manipulation_indicators",
                []
            ),
            "sources": result.get(
                "authenticity_indicators",
                []
            ),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "frames_analyzed": len(
                frames_to_analyze
            )
        }

        await save_to_history(
            "video",
            f"Video: {file.filename}",
            response_data,
            filename=file.filename
        )

        return response_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Video detection error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Video analysis failed: {str(e)}"
            )
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                logger.warning(
                    f"Could not remove temporary file: {temp_path}"
                )


# ============================================================
# Routes - News Verification
# ============================================================

@api_router.post("/verify-news")
async def verify_news(
    request: VerificationRequest
):
    """Verify a claim using News API + AI."""

    try:
        logger.info(
            f"Verifying claim: {request.claim}"
        )

        # News API is optional
        news_result = await verify_with_news_api(
            request.claim
        )

        # AI verification
        ai_result = await verify_claim_with_llm(
            request.claim
        )

        status_map = {
            "VERIFIED": "REAL",
            "PARTIALLY_VERIFIED": "UNCERTAIN",
            "UNVERIFIED": "FAKE"
        }

        response_data = {
            "status": status_map.get(
                ai_result.get(
                    "status",
                    "UNVERIFIED"
                ),
                "UNCERTAIN"
            ),
            "confidence": float(
                ai_result.get(
                    "confidence",
                    50
                )
            ),
            "explanation": ai_result.get(
                "explanation",
                "Verification completed"
            ),
            "explanation_english": ai_result.get(
                "explanation_english",
                ai_result.get(
                    "explanation",
                    ""
                )
            ),
            "detected_language": ai_result.get(
                "detected_language",
                "english"
            ),
            "suspicious_keywords": ai_result.get(
                "supporting_facts",
                []
            ),
            "sources": [
                ai_result.get(
                    "related_context",
                    ""
                )
            ],
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "news_api_available": (
                news_result is not None
            ),
            "matching_articles": (
                news_result.get(
                    "matching_articles",
                    []
                )
                if news_result
                else []
            ),
            "news_sources": (
                news_result.get(
                    "sources",
                    []
                )
                if news_result
                else []
            )
        }

        await save_to_history(
            "verification",
            request.claim,
            response_data
        )

        return response_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"News verification error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# News API Status
# ============================================================

@api_router.get("/news-api-status")
async def news_api_status():
    """Check whether News API is configured."""

    configured = (
        NEWS_API_KEY is not None
        and len(NEWS_API_KEY) > 0
    )

    return {
        "configured": configured,
        "message": (
            "News API is configured and active"
            if configured
            else
            "News API key not configured. "
            "Add NEWS_API_KEY to enable "
            "real-time news verification."
        )
    }


@api_router.post("/configure-news-api")
async def configure_news_api(
    request: NewsApiKeyRequest
):
    """Configure News API key at runtime."""

    global NEWS_API_KEY

    NEWS_API_KEY = request.api_key

    logger.info(
        "News API key configured at runtime"
    )

    return {
        "message": (
            "News API key configured successfully"
        ),
        "configured": True
    }


# ============================================================
# History
# ============================================================

@api_router.get("/history")
async def get_history(
    type: Optional[str] = Query(
        None,
        description=(
            "Filter by type: "
            "text, image, video, verification"
        )
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        0,
        ge=0
    )
):
    """Get analysis history."""

    try:

        if DEMO_MODE:
            history = demo_history

            if type:
                history = [
                    item
                    for item in history
                    if item.get("type") == type
                ]

            total = len(history)

            items = history[
                offset:offset + limit
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": items
            }

        query = {}

        if type:
            query["type"] = type

        total = await db.analysis_history.count_documents(
            query
        )

        cursor = (
            db.analysis_history
            .find(
                query,
                {"_id": 0}
            )
            .sort(
                "timestamp",
                -1
            )
            .skip(offset)
            .limit(limit)
        )

        history = await cursor.to_list(
            length=limit
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": history
        }

    except Exception as e:

        logger.error(
            f"History fetch error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@api_router.delete("/history")
async def clear_history(
    request: Optional[HistoryDeleteRequest] = None
):
    """
    Clear analysis history.

    If ids are provided, delete those entries.
    Otherwise delete all history.
    """

    try:

        if DEMO_MODE:

            global demo_history

            if request and request.ids:

                original_count = len(demo_history)

                demo_history = [
                    item
                    for item in demo_history
                    if item.get("id") not in request.ids
                ]

                deleted_count = (
                    original_count - len(demo_history)
                )

                return {
                    "message": (
                        f"Deleted {deleted_count} entries"
                    ),
                    "deleted_count": deleted_count
                }

            deleted_count = len(demo_history)

            demo_history.clear()

            return {
                "message": (
                    f"Cleared all history "
                    f"({deleted_count} entries)"
                ),
                "deleted_count": deleted_count
            }

        if request and request.ids:

            result = await db.analysis_history.delete_many(
                {
                    "id": {
                        "$in": request.ids
                    }
                }
            )

            return {
                "message": (
                    f"Deleted {result.deleted_count} entries"
                ),
                "deleted_count": result.deleted_count
            }

        result = await db.analysis_history.delete_many({})

        return {
            "message": (
                f"Cleared all history "
                f"({result.deleted_count} entries)"
            ),
            "deleted_count": result.deleted_count
        }

    except Exception as e:

        logger.error(
            f"History delete error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# Batch Image Processing
# ============================================================

@api_router.post("/batch-detect-images")
async def batch_detect_images(
    files: List[UploadFile] = File(...)
):
    """Batch process multiple images."""

    try:

        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Maximum 10 files per batch"
                )
            )

        results = []

        for i, file in enumerate(files):

            try:

                logger.info(
                    f"Batch processing image "
                    f"{i + 1}/{len(files)}: "
                    f"{file.filename}"
                )

                contents = await file.read()

                if not contents:
                    raise ValueError(
                        "Empty image file"
                    )

                image_base64 = base64.b64encode(
                    contents
                ).decode("utf-8")

                mime_type = get_image_mime_type(
                    file.content_type
                )

                result = await analyze_image_with_vision(
                    image_base64,
                    mime_type
                )

                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": result.get(
                        "status",
                        "UNKNOWN"
                    ),
                    "confidence": float(
                        result.get(
                            "confidence",
                            50
                        )
                    ),
                    "explanation": result.get(
                        "explanation",
                        "Analysis completed"
                    ),
                    "suspicious_keywords": result.get(
                        "manipulation_indicators",
                        []
                    ),
                    "sources": result.get(
                        "authenticity_indicators",
                        []
                    ),
                    "success": True
                }

                await save_to_history(
                    "image",
                    f"Batch Image: {file.filename}",
                    file_result,
                    filename=file.filename
                )

            except Exception as e:

                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": "ERROR",
                    "confidence": 0,
                    "explanation": (
                        f"Failed to analyze: {str(e)}"
                    ),
                    "suspicious_keywords": [],
                    "sources": [],
                    "success": False
                }

            results.append(file_result)

        return {
            "total_files": len(files),
            "successful": sum(
                1
                for result in results
                if result["success"]
            ),
            "failed": sum(
                1
                for result in results
                if not result["success"]
            ),
            "results": results,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Batch image detection error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# Batch Video Processing
# ============================================================

@api_router.post("/batch-detect-videos")
async def batch_detect_videos(
    files: List[UploadFile] = File(...)
):
    """Batch process multiple videos."""

    try:

        if len(files) > 5:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Maximum 5 videos per batch"
                )
            )

        results = []

        for i, file in enumerate(files):

            temp_path = None

            try:

                logger.info(
                    f"Batch processing video "
                    f"{i + 1}/{len(files)}: "
                    f"{file.filename}"
                )

                if not file.filename:
                    raise ValueError(
                        "No filename provided"
                    )

                valid_extensions = [
                    ".mp4",
                    ".mov",
                    ".avi",
                    ".mkv",
                    ".webm"
                ]

                file_ext = os.path.splitext(
                    file.filename.lower()
                )[1]

                if file_ext not in valid_extensions:
                    raise ValueError(
                        f"Unsupported format: {file_ext}"
                    )

                contents = await file.read()

                if not contents:
                    raise ValueError(
                        "Empty file"
                    )

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_ext
                ) as temp_file:

                    temp_path = temp_file.name
                    temp_file.write(contents)

                cap = cv2.VideoCapture(
                    temp_path
                )

                if not cap.isOpened():
                    raise ValueError(
                        "Unable to open video file"
                    )

                ret, frame = cap.read()

                cap.release()

                if not ret:
                    raise ValueError(
                        "Could not extract frame "
                        "from video"
                    )

                success, buffer = cv2.imencode(
                    ".jpg",
                    frame
                )

                if not success:
                    raise ValueError(
                        "Could not encode video frame"
                    )

                frame_base64 = base64.b64encode(
                    buffer
                ).decode("utf-8")

                result = await analyze_image_with_vision(
                    frame_base64,
                    "image/jpeg"
                )

                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": result.get(
                        "status",
                        "UNKNOWN"
                    ),
                    "confidence": float(
                        result.get(
                            "confidence",
                            50
                        )
                    ),
                    "explanation": result.get(
                        "explanation",
                        "Video analysis completed"
                    ),
                    "suspicious_keywords": result.get(
                        "manipulation_indicators",
                        []
                    ),
                    "sources": result.get(
                        "authenticity_indicators",
                        []
                    ),
                    "success": True
                }

                await save_to_history(
                    "video",
                    f"Batch Video: {file.filename}",
                    file_result,
                    filename=file.filename
                )

            except Exception as e:

                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": "ERROR",
                    "confidence": 0,
                    "explanation": (
                        f"Failed to analyze: {str(e)}"
                    ),
                    "suspicious_keywords": [],
                    "sources": [],
                    "success": False
                }

            finally:

                if (
                    temp_path
                    and os.path.exists(temp_path)
                ):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        logger.warning(
                            f"Could not remove "
                            f"temporary file: {temp_path}"
                        )

            results.append(file_result)

        return {
            "total_files": len(files),
            "successful": sum(
                1
                for result in results
                if result["success"]
            ),
            "failed": sum(
                1
                for result in results
                if not result["success"]
            ),
            "results": results,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Batch video detection error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# Include Router
# ============================================================

app.include_router(api_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get(
        "CORS_ORIGINS",
        "*"
    ).split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Shutdown
# ============================================================

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()
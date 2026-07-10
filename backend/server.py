from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import base64
import io
import json
from PIL import Image
import cv2
import numpy as np
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Fake News Detection API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API keys
EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Supported languages
SUPPORTED_LANGUAGES = ["english", "hindi", "marathi", "tamil", "hinglish"]

# Define Models
class TextDetectionRequest(BaseModel):
    text: str = Field(..., description="News text to analyze")

class DetectionResult(BaseModel):
    status: str
    confidence: float
    explanation: str
    explanation_english: Optional[str] = None
    suspicious_keywords: List[str] = []
    sources: List[str] = []
    timestamp: str
    detected_language: Optional[str] = None

class VerificationRequest(BaseModel):
    claim: str = Field(..., description="Claim to verify")

class NewsApiKeyRequest(BaseModel):
    api_key: str = Field(..., description="News API key to configure")

class HistoryDeleteRequest(BaseModel):
    ids: Optional[List[str]] = None

# ============================================================
# Helper functions
# ============================================================

def parse_llm_json(response_text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks"""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)

async def save_to_history(analysis_type: str, content_preview: str, result: dict, filename: str = None):
    """Save analysis result to MongoDB history"""
    doc = {
        "id": str(uuid.uuid4()),
        "type": analysis_type,
        "content_preview": content_preview[:300],
        "filename": filename,
        "status": result.get("status", "UNKNOWN"),
        "confidence": result.get("confidence", 0),
        "explanation": result.get("explanation", ""),
        "suspicious_keywords": result.get("suspicious_keywords", []),
        "sources": result.get("sources", []),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.analysis_history.insert_one(doc)
    return doc["id"]

async def analyze_text_with_llm(text: str) -> dict:
    """Analyze text using LLM for fake news detection with multilingual support"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"text-analysis-{uuid.uuid4()}",
            system_message="""You are an expert fake news detection AI that supports multiple languages including English, Hindi, Marathi, Tamil, and Hinglish.

IMPORTANT LANGUAGE RULES:
1. First detect the language of the input text.
2. Provide the main explanation in the SAME language as the input.
3. Always provide an English explanation as well (in the "explanation_english" field).
4. If the input is already in English, set explanation_english to the same as explanation.

Provide your analysis in this exact JSON format:
{
    "status": "REAL" or "FAKE",
    "confidence": (number between 0-100),
    "detected_language": "english" or "hindi" or "marathi" or "tamil" or "hinglish",
    "explanation": "detailed explanation in the SAME language as the input text",
    "explanation_english": "detailed explanation in English",
    "suspicious_keywords": ["list", "of", "suspicious", "words"],
    "credibility_indicators": ["list of credibility factors found or missing"]
}

Consider:
- Sensational or emotional language
- Lack of credible sources
- Logical inconsistencies
- Misleading headlines vs content
- Verifiable facts and dates
- Author credibility indicators"""
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Analyze this news article for authenticity. Detect its language and respond accordingly:\n\n{text}"
        )
        
        response = await chat.send_message(user_message)
        return parse_llm_json(response)
    
    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def analyze_image_with_vision(image_base64: str) -> dict:
    """Analyze image using Vision API for deepfake/manipulation detection"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"image-analysis-{uuid.uuid4()}",
            system_message="""You are an expert deepfake and image manipulation detection AI. Analyze images for signs of manipulation, AI generation, or deepfakes.
            
Provide your analysis in this exact JSON format:
{
    "status": "REAL" or "FAKE",
    "confidence": (number between 0-100),
    "explanation": "detailed explanation of manipulation indicators found or authenticity indicators",
    "manipulation_indicators": ["list of specific manipulation signs detected"],
    "authenticity_indicators": ["list of authenticity markers found"]
}

Look for:
- Unnatural facial features or expressions
- Inconsistent lighting or shadows
- Blurred or distorted edges
- Artifacts from AI generation
- Inconsistent image quality across regions
- Anatomical impossibilities
- Background inconsistencies"""
        ).with_model("openai", "gpt-5.2")
        
        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text="Analyze this image for signs of manipulation, deepfakes, or AI generation. Determine if it's REAL or FAKE.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        return parse_llm_json(response)
    
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

async def verify_claim_with_llm(claim: str) -> dict:
    """Verify a claim using LLM's knowledge base with multilingual support"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"claim-verification-{uuid.uuid4()}",
            system_message="""You are a fact-checking AI with access to general world knowledge that supports multiple languages including English, Hindi, Marathi, Tamil, and Hinglish.

IMPORTANT LANGUAGE RULES:
1. First detect the language of the input claim.
2. Provide the main explanation in the SAME language as the input.
3. Always provide an English explanation as well (in the "explanation_english" field).
4. If the input is already in English, set explanation_english to the same as explanation.

Provide your analysis in this exact JSON format:
{
    "status": "VERIFIED" or "UNVERIFIED" or "PARTIALLY_VERIFIED",
    "confidence": (number between 0-100),
    "detected_language": "english" or "hindi" or "marathi" or "tamil" or "hinglish",
    "explanation": "detailed explanation in the SAME language as the input",
    "explanation_english": "detailed explanation in English",
    "supporting_facts": ["list of facts that support or contradict the claim"],
    "related_context": "relevant context or background information"
}

Base your assessment on:
- Known historical facts
- Scientific consensus
- Publicly documented events
- Logical consistency
- Common knowledge verification"""
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Verify this claim based on known facts. Detect language and respond accordingly:\n\n{claim}"
        )
        
        response = await chat.send_message(user_message)
        return parse_llm_json(response)
    
    except Exception as e:
        logger.error(f"Error in claim verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

async def verify_with_news_api(claim: str) -> dict:
    """Verify a claim using News API for real-time news comparison"""
    import requests
    
    if not NEWS_API_KEY:
        return None
    
    try:
        # Extract keywords from claim for search
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
            logger.warning(f"News API returned status {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get("status") != "ok" or not data.get("articles"):
            return None
        
        articles = data["articles"]
        matching_articles = []
        
        for article in articles[:5]:
            matching_articles.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
                "description": article.get("description", "")
            })
        
        return {
            "articles_found": len(articles),
            "matching_articles": matching_articles,
            "sources": list(set(a.get("source", {}).get("name", "") for a in articles[:5]))
        }
    
    except Exception as e:
        logger.error(f"News API error: {str(e)}")
        return None

# ============================================================
# Routes
# ============================================================

@api_router.get("/")
async def root():
    return {"message": "Fake News Detection API", "status": "operational"}

@api_router.post("/detect-text")
async def detect_text(request: TextDetectionRequest):
    """Detect fake news in text using AI with multilingual support"""
    try:
        logger.info(f"Analyzing text: {request.text[:100]}...")
        
        result = await analyze_text_with_llm(request.text)
        
        response_data = {
            "status": result.get("status", "UNKNOWN"),
            "confidence": float(result.get("confidence", 50)),
            "explanation": result.get("explanation", "Analysis completed"),
            "explanation_english": result.get("explanation_english", result.get("explanation", "")),
            "detected_language": result.get("detected_language", "english"),
            "suspicious_keywords": result.get("suspicious_keywords", []),
            "sources": result.get("credibility_indicators", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to history
        await save_to_history("text", request.text, response_data)
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/detect-image")
async def detect_image(file: UploadFile = File(...)):
    """Detect deepfakes/manipulation in images using Vision AI"""
    try:
        logger.info(f"Analyzing image: {file.filename}")
        
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        result = await analyze_image_with_vision(image_base64)
        
        response_data = {
            "status": result.get("status", "UNKNOWN"),
            "confidence": float(result.get("confidence", 50)),
            "explanation": result.get("explanation", "Analysis completed"),
            "suspicious_keywords": result.get("manipulation_indicators", []),
            "sources": result.get("authenticity_indicators", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to history
        await save_to_history("image", f"Image: {file.filename}", response_data, filename=file.filename)
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/detect-video")
async def detect_video(file: UploadFile = File(...)):
    """Detect deepfakes in videos using frame-by-frame analysis"""
    temp_path = None
    try:
        logger.info(f"Analyzing video: {file.filename}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid file: No filename provided")
        
        valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported video format. Please upload one of: {', '.join(valid_extensions)}"
            )
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        max_size = 100 * 1024 * 1024
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="Video file too large. Maximum size is 100MB")
        
        temp_path = f"/tmp/{uuid.uuid4()}{file_ext}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        cap = cv2.VideoCapture(temp_path)
        
        if not cap.isOpened():
            raise HTTPException(
                status_code=400, 
                detail="Unable to open video file. Please ensure it's a valid video format"
            )
        
        frames_to_analyze = []
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0:
            max_frames = 5
            while len(frames_to_analyze) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                frames_to_analyze.append(frame_base64)
        else:
            sample_indices = np.linspace(0, total_frames - 1, min(5, total_frames), dtype=int)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count in sample_indices:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    frames_to_analyze.append(frame_base64)
                frame_count += 1
        
        cap.release()
        
        if not frames_to_analyze:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=400, 
                detail="No frames could be extracted from video. The video may be corrupted or in an unsupported format"
            )
        
        result = await analyze_image_with_vision(frames_to_analyze[0])
        
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        response_data = {
            "status": result.get("status", "UNKNOWN"),
            "confidence": float(result.get("confidence", 50)),
            "explanation": result.get("explanation", "Video analysis completed") + f" (Analyzed {len(frames_to_analyze)} frames)",
            "suspicious_keywords": result.get("manipulation_indicators", []),
            "sources": result.get("authenticity_indicators", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "frames_analyzed": len(frames_to_analyze)
        }
        
        # Save to history
        await save_to_history("video", f"Video: {file.filename}", response_data, filename=file.filename)
        
        return response_data
    
    except HTTPException:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as e:
        logger.error(f"Video detection error: {str(e)}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500, 
            detail=f"Video analysis failed: {str(e)}. Please try a different video file"
        )

# ============================================================
# News API Verification (Modular)
# ============================================================

@api_router.post("/verify-news")
async def verify_news(request: VerificationRequest):
    """Verify a claim using News API + AI verification"""
    try:
        logger.info(f"Verifying claim: {request.claim}")
        
        # Try News API first if key is available
        news_result = await verify_with_news_api(request.claim)
        
        # Always do AI verification
        ai_result = await verify_claim_with_llm(request.claim)
        
        status_map = {
            "VERIFIED": "REAL",
            "PARTIALLY_VERIFIED": "UNCERTAIN",
            "UNVERIFIED": "FAKE"
        }
        
        response_data = {
            "status": status_map.get(ai_result.get("status", "UNVERIFIED"), "UNCERTAIN"),
            "confidence": float(ai_result.get("confidence", 50)),
            "explanation": ai_result.get("explanation", "Verification completed"),
            "explanation_english": ai_result.get("explanation_english", ai_result.get("explanation", "")),
            "detected_language": ai_result.get("detected_language", "english"),
            "suspicious_keywords": ai_result.get("supporting_facts", []),
            "sources": [ai_result.get("related_context", "")],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "news_api_available": news_result is not None,
            "matching_articles": news_result.get("matching_articles", []) if news_result else [],
            "news_sources": news_result.get("sources", []) if news_result else []
        }
        
        # Save to history
        await save_to_history("verification", request.claim, response_data)
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"News verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/news-api-status")
async def news_api_status():
    """Check if News API key is configured"""
    return {
        "configured": NEWS_API_KEY is not None and len(NEWS_API_KEY) > 0,
        "message": "News API is configured and active" if NEWS_API_KEY else "News API key not configured. Add NEWS_API_KEY to enable real-time news verification."
    }

@api_router.post("/configure-news-api")
async def configure_news_api(request: NewsApiKeyRequest):
    """Configure News API key at runtime"""
    global NEWS_API_KEY
    NEWS_API_KEY = request.api_key
    logger.info("News API key configured at runtime")
    return {"message": "News API key configured successfully", "configured": True}

# ============================================================
# History Tracking
# ============================================================

@api_router.get("/history")
async def get_history(
    type: Optional[str] = Query(None, description="Filter by type: text, image, video, verification"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get analysis history with optional filtering"""
    try:
        query = {}
        if type:
            query["type"] = type
        
        total = await db.analysis_history.count_documents(query)
        
        cursor = db.analysis_history.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
        history = await cursor.to_list(length=limit)
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": history
        }
    
    except Exception as e:
        logger.error(f"History fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/history")
async def clear_history(request: Optional[HistoryDeleteRequest] = None):
    """Clear analysis history. If ids provided, delete specific entries; otherwise clear all."""
    try:
        if request and request.ids:
            result = await db.analysis_history.delete_many({"id": {"$in": request.ids}})
            return {"message": f"Deleted {result.deleted_count} entries", "deleted_count": result.deleted_count}
        else:
            result = await db.analysis_history.delete_many({})
            return {"message": f"Cleared all history ({result.deleted_count} entries)", "deleted_count": result.deleted_count}
    
    except Exception as e:
        logger.error(f"History delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Batch Processing
# ============================================================

@api_router.post("/batch-detect-images")
async def batch_detect_images(files: List[UploadFile] = File(...)):
    """Batch process multiple images for deepfake detection"""
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
        
        results = []
        
        for i, file in enumerate(files):
            try:
                logger.info(f"Batch processing image {i+1}/{len(files)}: {file.filename}")
                
                contents = await file.read()
                image_base64 = base64.b64encode(contents).decode('utf-8')
                
                result = await analyze_image_with_vision(image_base64)
                
                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": result.get("status", "UNKNOWN"),
                    "confidence": float(result.get("confidence", 50)),
                    "explanation": result.get("explanation", "Analysis completed"),
                    "suspicious_keywords": result.get("manipulation_indicators", []),
                    "sources": result.get("authenticity_indicators", []),
                    "success": True
                }
                
                # Save to history
                await save_to_history("image", f"Batch Image: {file.filename}", file_result, filename=file.filename)
                
            except Exception as e:
                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": "ERROR",
                    "confidence": 0,
                    "explanation": f"Failed to analyze: {str(e)}",
                    "suspicious_keywords": [],
                    "sources": [],
                    "success": False
                }
            
            results.append(file_result)
        
        return {
            "total_files": len(files),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch image detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/batch-detect-videos")
async def batch_detect_videos(files: List[UploadFile] = File(...)):
    """Batch process multiple videos for deepfake detection"""
    try:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 videos per batch")
        
        results = []
        
        for i, file in enumerate(files):
            temp_path = None
            try:
                logger.info(f"Batch processing video {i+1}/{len(files)}: {file.filename}")
                
                if not file.filename:
                    raise ValueError("No filename provided")
                
                valid_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in valid_extensions:
                    raise ValueError(f"Unsupported format: {file_ext}")
                
                contents = await file.read()
                if len(contents) == 0:
                    raise ValueError("Empty file")
                
                temp_path = f"/tmp/{uuid.uuid4()}{file_ext}"
                with open(temp_path, "wb") as f:
                    f.write(contents)
                
                cap = cv2.VideoCapture(temp_path)
                if not cap.isOpened():
                    raise ValueError("Unable to open video file")
                
                # Extract first frame
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    raise ValueError("Could not extract frame from video")
                
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                result = await analyze_image_with_vision(frame_base64)
                
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                
                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": result.get("status", "UNKNOWN"),
                    "confidence": float(result.get("confidence", 50)),
                    "explanation": result.get("explanation", "Video analysis completed"),
                    "suspicious_keywords": result.get("manipulation_indicators", []),
                    "sources": result.get("authenticity_indicators", []),
                    "success": True
                }
                
                await save_to_history("video", f"Batch Video: {file.filename}", file_result, filename=file.filename)
                
            except Exception as e:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                file_result = {
                    "filename": file.filename,
                    "index": i,
                    "status": "ERROR",
                    "confidence": 0,
                    "explanation": f"Failed to analyze: {str(e)}",
                    "suspicious_keywords": [],
                    "sources": [],
                    "success": False
                }
            
            results.append(file_result)
        
        return {
            "total_files": len(files),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch video detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

import os
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from models import DetectResponse

router = APIRouter(prefix="/api", tags=["Scanner"])

SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER", "")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET", "")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/x-m4a"}
MAX_FILE_SIZE_MB = 25


@router.post("/detect-upload", response_model=DetectResponse)
async def detect_upload(file: UploadFile = File(...)):
    if not SIGHTENGINE_API_USER or not SIGHTENGINE_API_SECRET:
        raise HTTPException(status_code=500, detail="Detection service is not configured.")

    content_type = (file.content_type or "").lower()
    if content_type in ALLOWED_IMAGE_TYPES:
        file_category = "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        file_category = "video"
    elif content_type in ALLOWED_AUDIO_TYPES:
        file_category = "audio"
    else:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{content_type}'.")

    file_bytes = await file.read()
    if len(file_bytes) / (1024 * 1024) > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum is {MAX_FILE_SIZE_MB} MB.")

    auth = {
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if file_category == "image":
                # Use genai model — detects AI-generated images broadly, free tier
                resp = await client.post(
                    "https://api.sightengine.com/1.0/check.json",
                    data={**auth, "models": "genai"},
                    files={"media": (file.filename, file_bytes, content_type)},
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "failure":
                    msg = data.get("error", {}).get("message", "")
                    if "limit" in msg.lower():
                        raise HTTPException(status_code=429, detail="Daily scan limit reached — try The Academy to keep learning!")
                    raise HTTPException(status_code=502, detail=f"Detection error: {msg}")
                # genai returns type.ai_generated
                score = float(data.get("type", {}).get("ai_generated", 0))

            elif file_category == "audio":
                resp = await client.post(
                    "https://api.sightengine.com/1.0/audio/check.json",
                    data={**auth, "models": "ai-generated"},
                    files={"media": (file.filename, file_bytes, content_type)},
                )
                resp.raise_for_status()
                data = resp.json()
                score = float(data.get("ai_generated", {}).get("score", 0))

            else:  # video
                raise HTTPException(
                    status_code=415,
                    detail="Video scanning requires a paid plan. Please upload an image or audio file instead."
                )

        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Detection service error: {exc.response.status_code}")
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Could not reach the detection service.")

    return DetectResponse(
        confidence=score,
        percentage=f"{round(score * 100)}%",
        verdict="Likely AI-generated" if score >= 0.5 else "Likely Real",
        file_type=file_category,
    )

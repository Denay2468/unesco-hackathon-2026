import os
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from models import DetectResponse

router = APIRouter(prefix="/api", tags=["Scanner"])

SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER", "")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET", "")

IMAGE_ENDPOINT = "https://api.sightengine.com/1.0/check.json"
VIDEO_ENDPOINT = "https://api.sightengine.com/1.0/video/check-sync.json"
AUDIO_ENDPOINT = "https://api.sightengine.com/1.0/audio/check.json"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/x-m4a"}

MAX_FILE_SIZE_MB = 25


def _check_rate_limit(response_data: dict) -> bool:
    """Return True if Sightengine returned a rate-limit error."""
    return (
        response_data.get("status") == "failure"
        and "limit" in str(response_data.get("error", {}).get("message", "")).lower()
    )


def _extract_image_confidence(data: dict) -> float:
    """Pull deepfake probability from Sightengine image response."""
    try:
        return float(data["type"]["deepfake"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def _extract_video_confidence(data: dict) -> float:
    """
    For sync video check, Sightengine returns per-frame data.
    We take the max deepfake score across all frames.
    """
    try:
        frames = data.get("data", {}).get("frames", [])
        if not frames:
            return 0.0
        scores = [float(f.get("deepfake", {}).get("score", 0)) for f in frames]
        return max(scores)
    except (KeyError, TypeError, ValueError):
        return 0.0


def _extract_audio_confidence(data: dict) -> float:
    """Pull ai-generated probability from Sightengine audio response."""
    try:
        return float(data["ai_generated"]["score"])
    except (KeyError, TypeError, ValueError):
        return 0.0


@router.post("/detect-upload", response_model=DetectResponse)
async def detect_upload(file: UploadFile = File(...)):
    # ── Validate credentials ────────────────────────────────────────────
    if not SIGHTENGINE_API_USER or not SIGHTENGINE_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Detection service is not configured. Contact the administrator.",
        )

    # ── Detect file category ────────────────────────────────────────────
    content_type = (file.content_type or "").lower()

    if content_type in ALLOWED_IMAGE_TYPES:
        file_category = "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        file_category = "video"
    elif content_type in ALLOWED_AUDIO_TYPES:
        file_category = "audio"
    else:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{content_type}'. "
                "Please upload an image (JPEG/PNG/WebP), video (MP4/WebM), "
                "or audio (MP3/WAV/OGG) file."
            ),
        )

    # ── Read file bytes ─────────────────────────────────────────────────
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed size is {MAX_FILE_SIZE_MB} MB.",
        )

    auth_params = {
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if file_category == "image":
                resp = await client.post(
                    IMAGE_ENDPOINT,
                    data={**auth_params, "models": "deepfake"},
                    files={"media": (file.filename, file_bytes, content_type)},
                )
                resp.raise_for_status()
                data = resp.json()
                if _check_rate_limit(data):
                    raise HTTPException(
                        status_code=429,
                        detail="Daily scan limit reached — try The Academy to keep learning!",
                    )
                confidence = _extract_image_confidence(data)

            elif file_category == "video":
                resp = await client.post(
                    VIDEO_ENDPOINT,
                    data={**auth_params, "models": "deepfake"},
                    files={"media": (file.filename, file_bytes, content_type)},
                )
                resp.raise_for_status()
                data = resp.json()
                if _check_rate_limit(data):
                    raise HTTPException(
                        status_code=429,
                        detail="Daily scan limit reached — try The Academy to keep learning!",
                    )
                confidence = _extract_video_confidence(data)

            else:  # audio
                resp = await client.post(
                    AUDIO_ENDPOINT,
                    data={**auth_params, "models": "ai-generated"},
                    files={"media": (file.filename, file_bytes, content_type)},
                )
                resp.raise_for_status()
                data = resp.json()
                if _check_rate_limit(data):
                    raise HTTPException(
                        status_code=429,
                        detail="Daily scan limit reached — try The Academy to keep learning!",
                    )
                confidence = _extract_audio_confidence(data)

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Detection service returned an error: {exc.response.status_code}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail="Could not reach the detection service. Please try again later.",
            )

    verdict = "Likely AI-generated" if confidence >= 0.5 else "Likely Real"
    percentage = f"{round(confidence * 100)}%"

    return DetectResponse(
        confidence=confidence,
        percentage=percentage,
        verdict=verdict,
        file_type=file_category,
    )

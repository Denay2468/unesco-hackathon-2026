import os
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# For Supabase PostgreSQL, connection pooling via pgBouncer requires
# ?pgbouncer=true in the URL. The Supabase "Transaction" pooler URL already
# handles this — just paste it as DATABASE_URL in your Render env vars.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    # Required for SQLite only (ignored by PostgreSQL driver)
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# ── Seed helper (run once to populate the database) ───────────────────────

SEED_CASES = [
    {
        "title": "The Fake Mayor Audio Leak",
        "story": (
            "Just three days before the municipal election, an anonymous Telegram "
            "channel published a 47-second audio clip. In it, Mayor Elena Vasquez "
            "appears to confess to accepting bribes from a real-estate developer. "
            "The recording went viral overnight. Your job: determine whether this "
            "clip is genuine or fabricated."
        ),
        "media_url": "https://cdn.deepfakedetective.app/cases/mayor-audio.mp3",
        "media_type": "audio",
        "correct_answer": "fake",
        "explanation": (
            "This clip is AI-generated. Voice-cloning tools like ElevenLabs can "
            "produce convincing audio from as little as 30 seconds of source material. "
            "Forensic analysis revealed unnatural micro-pauses between phonemes, "
            "a compressed frequency range at 3 kHz–5 kHz (a hallmark of TTS synthesis), "
            "and metadata showing the file was created four hours before 'leaking'. "
            "Always verify audio with multiple independent sources before sharing."
        ),
    },
    {
        "title": "The CEO Resignation Video",
        "story": (
            "TechVenture Inc.'s stock dropped 18 % after a video surfaced showing "
            "CEO Marcus Chen announcing an unexpected resignation and 'accounting "
            "irregularities'. The company denies it. Shareholders are panicking. "
            "You have 10 minutes to call it: real or deepfake?"
        ),
        "media_url": "https://cdn.deepfakedetective.app/cases/ceo-video.mp4",
        "media_type": "video",
        "correct_answer": "fake",
        "explanation": (
            "The video is a face-swap deepfake. Key tells: the eye-blink rate is "
            "roughly half the normal human average (suggesting the model was trained "
            "on photos rather than video), lighting on the face doesn't match the "
            "background light source, and a 3-pixel 'edge shimmer' is visible around "
            "the hairline — a GAN blending artefact. Market-manipulating deepfakes "
            "are increasingly common; treat unverified corporate announcements with "
            "extreme caution."
        ),
    },
    {
        "title": "The Protest Photograph",
        "story": (
            "A photograph is circulating on social media purportedly showing a "
            "violent confrontation at last Saturday's climate rally. News outlets "
            "are split — some ran it, some held back. Witnesses at the rally say "
            "nothing like this happened. Investigate the image."
        ),
        "media_url": "https://cdn.deepfakedetective.app/cases/protest-photo.jpg",
        "media_type": "image",
        "correct_answer": "fake",
        "explanation": (
            "The image was AI-generated using Midjourney v6. Reverse image search "
            "finds no prior publication; the EXIF data is absent entirely (authentic "
            "press photos carry camera metadata). Lighting analysis shows the crowd "
            "casts shadows in three different directions — physically impossible in "
            "a single scene. AI image generators still struggle with coherent global "
            "lighting and hands (notice the officer's left hand has six fingers)."
        ),
    },
    {
        "title": "The Politician's Confession",
        "story": (
            "A clip of Senator Diana Okafor appears to show her admitting 'off camera' "
            "that her climate policy is 'all for show'. Her opponents shared it widely. "
            "Her office calls it fabricated. The original source cannot be traced. "
            "What does the evidence say?"
        ),
        "media_url": "https://cdn.deepfakedetective.app/cases/senator-clip.mp4",
        "media_type": "video",
        "correct_answer": "real",
        "explanation": (
            "This clip is real — it is a decontextualised excerpt from a satirical "
            "sketch the senator performed at a charity gala two years ago. The 'confession' "
            "is a scripted joke delivered to a laughing audience. The full 4-minute "
            "video is publicly available. This case illustrates 'cheapfake' manipulation: "
            "no AI needed, just selective cropping and misleading captions. Context "
            "is everything."
        ),
    },
]

SEED_CLUES = [
    # Case 1 — Mayor Audio
    {"case_id": 1, "tool_type": "voice_artifacts", "clue_text": "Spectral analysis shows an anomalous frequency notch at 3.2 kHz–4.8 kHz consistent with neural TTS synthesis. Natural human speech fills this band continuously."},
    {"case_id": 1, "tool_type": "metadata", "clue_text": "File creation timestamp: 2024-03-11 02:14 UTC. The alleged recording date was 2024-03-11, but investigative timelines show the mayor was in a public council session at that exact time."},
    {"case_id": 1, "tool_type": "reverse_image", "clue_text": "Audio fingerprint search finds no prior broadcast of this clip. Authentic leaked recordings typically appear on multiple platforms within minutes; this one emerged from a single anonymous account."},
    # Case 2 — CEO Video
    {"case_id": 2, "tool_type": "lighting", "clue_text": "The key light on the subject's face comes from the upper-right, but the background window light source is upper-left. Real video cannot have two conflicting primary light directions."},
    {"case_id": 2, "tool_type": "metadata", "clue_text": "Video encoding metadata shows two distinct creation timestamps 11 minutes apart — evidence of re-encoding after compositing. Original camera files contain a single unbroken timestamp chain."},
    {"case_id": 2, "tool_type": "voice_artifacts", "clue_text": "Blink frequency: 4 blinks/minute (normal: 15–20). Face-swap models trained on still images consistently under-generate blinks. Prolonged staring is a reliable early signal."},
    # Case 3 — Protest Photo
    {"case_id": 3, "tool_type": "lighting", "clue_text": "Shadow vectors for crowd members on the left fall south-east; shadows for the central group fall south-west; background figures cast no shadows at all. No real-world lighting setup produces this."},
    {"case_id": 3, "tool_type": "metadata", "clue_text": "EXIF data is completely absent. Authentic photojournalism images carry GPS, camera model, shutter speed, and ISO. Stripped metadata or absent metadata on a 'news photo' is a red flag."},
    {"case_id": 3, "tool_type": "reverse_image", "clue_text": "Reverse image search returns zero prior results. A real protest photo from a news event would be indexed by at least one wire service within hours of the event occurring."},
    # Case 4 — Senator Clip
    {"case_id": 4, "tool_type": "lighting", "clue_text": "Lighting is perfectly consistent across the entire frame. No blending artefacts. The colour temperature matches a professional stage rig — not a hidden camera."},
    {"case_id": 4, "tool_type": "metadata", "clue_text": "Encoding metadata traces to a Sony FX3 cinema camera. The original file hash matches event footage from the 2022 Okafor Foundation Gala archived on the foundation's own website."},
    {"case_id": 4, "tool_type": "reverse_image", "clue_text": "Reverse video search finds the full 4-minute original on YouTube (uploaded 2022-09-14). The circulating clip is seconds 1:42–2:08, cutting immediately before the punchline and the audience laughter."},
]


def seed_database(session: Session):
    from models import Case, Clue
    from sqlmodel import select

    existing = session.exec(select(Case)).first()
    if existing:
        return  # already seeded

    for c in SEED_CASES:
        session.add(Case(**c))
    session.commit()

    # Re-fetch to get auto-assigned IDs (handles both SQLite & Postgres)
    cases = session.exec(select(Case).order_by(Case.id)).all()
    id_map = {i + 1: cases[i].id for i in range(len(cases))}

    for clue_data in SEED_CLUES:
        real_case_id = id_map.get(clue_data["case_id"], clue_data["case_id"])
        session.add(Clue(case_id=real_case_id, tool_type=clue_data["tool_type"], clue_text=clue_data["clue_text"]))
    session.commit()

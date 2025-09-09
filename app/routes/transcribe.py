import os
import uuid
import shutil
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from ..whisper_utils import get_model, detect_first_speech
from ..utils import seconds_to_hms, format_srt_time, split_segment_text_precise, generate_srt

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/transcribe")
async def transcribe_text(
    video: UploadFile = File(...),
    with_timestamps: str = Form("0"),
    split_segments: str = Form("0")
):
    unique_filename = f"{uuid.uuid4()}_{video.filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        whisper_model = get_model()
        first_speech_time = detect_first_speech(save_path)

        segments, _ = whisper_model.transcribe(
            save_path,
            beam_size=5,
            initial_prompt=None,
            condition_on_previous_text=False,
        )

        transcription = []
        first_adjusted = False

        for seg in segments:
            if split_segments == "1":
                subs = split_segment_text_precise(seg.text, seg.start, seg.end)
                for sub in subs:
                    entry = {"text": sub["text"].strip()}
                    s_start, s_end = sub["start"], sub["end"]
                    if not first_adjusted and first_speech_time > 0:
                        s_start = first_speech_time
                        first_adjusted = True
                    if with_timestamps == "1":
                        entry["start"] = seconds_to_hms(s_start)
                        entry["end"] = seconds_to_hms(s_end)
                    transcription.append(entry)
            else:
                entry = {"text": seg.text.strip()}
                s_start, s_end = seg.start, seg.end
                if not first_adjusted and first_speech_time > 0:
                    s_start = first_speech_time
                    first_adjusted = True
                if with_timestamps == "1":
                    entry["start"] = seconds_to_hms(s_start)
                    entry["end"] = seconds_to_hms(s_end)
                transcription.append(entry)

        return {"transcription": transcription}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process transcription: {str(e)}")

    finally:
        if os.path.exists(save_path):
            os.remove(save_path)


@router.post("/transcribe_srt")
async def transcribe_to_srt(video: UploadFile = File(...)):
    unique_filename = f"{uuid.uuid4()}_{video.filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        whisper_model = get_model()
        first_speech_time = detect_first_speech(save_path)

        segments, _ = whisper_model.transcribe(
            save_path,
            beam_size=5,
            initial_prompt=None,
            condition_on_previous_text=False,
        )

        srt_content = generate_srt(segments, first_speech_time)
        srt_filename = unique_filename.rsplit(".", 1)[0] + ".srt"
        srt_path = os.path.join(UPLOAD_DIR, srt_filename)

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return FileResponse(srt_path, media_type="text/plain", filename=srt_filename)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate SRT: {str(e)}")

    finally:
        if os.path.exists(save_path):
            os.remove(save_path)

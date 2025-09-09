import os, uuid, shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from ..utils.security import get_current_user
from ..utils.whisper_utils import get_model, seconds_to_hms, split_segment_text_precise, format_srt_time
from ..utils.vad_utils import detect_first_speech

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/transcribe")
def transcribe_text(
    video: UploadFile = File(...),
    with_timestamps: str = Form("0"),
    split_segments: str = Form("0"),
    current_user: str = Depends(get_current_user)
):
    unique_filename = f"{uuid.uuid4()}_{video.filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

        whisper_model = get_model()
        first_speech_time = detect_first_speech(save_path)

        segments, _ = whisper_model.transcribe(save_path, beam_size=5)

        transcription, first_adjusted = [], False
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
                        entry["start"], entry["end"] = seconds_to_hms(s_start), seconds_to_hms(s_end)
                    transcription.append(entry)
            else:
                entry = {"text": seg.text.strip()}
                s_start, s_end = seg.start, seg.end
                if not first_adjusted and first_speech_time > 0:
                    s_start = first_speech_time
                    first_adjusted = True
                if with_timestamps == "1":
                    entry["start"], entry["end"] = seconds_to_hms(s_start), seconds_to_hms(s_end)
                transcription.append(entry)

        return {"transcription": transcription}

    finally:
        if os.path.exists(save_path):
            os.remove(save_path)

def generate_srt(segments, first_speech_time: float = 0.0, max_chars_per_line: int = 40):
    lines, first_adjusted = [], False
    for seg in segments:
        start, end = seg.start, seg.end
        if not first_adjusted and first_speech_time > 0:
            start = first_speech_time
            first_adjusted = True
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        words, current_line, wrapped = seg.text.strip().split(), "", []
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars_per_line:
                current_line += (" " if current_line else "") + word
            else:
                wrapped.append(current_line)
                current_line = word
        if current_line: wrapped.append(current_line)
        if len(wrapped) > 2: wrapped = [wrapped[0], " ".join(wrapped[1:])]
        lines.extend(wrapped); lines.append("")
    return "\n".join(lines)

@router.post("/transcribe_srt")
def transcribe_to_srt(video: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    unique_filename = f"{uuid.uuid4()}_{video.filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(save_path, "wb") as f: shutil.copyfileobj(video.file, f)

        whisper_model = get_model()
        first_speech_time = detect_first_speech(save_path)
        segments, _ = whisper_model.transcribe(save_path, beam_size=5)

        srt_content = generate_srt(segments, first_speech_time)
        srt_filename, srt_path = unique_filename.rsplit(".", 1)[0] + ".srt", os.path.join(UPLOAD_DIR, unique_filename.rsplit(".", 1)[0] + ".srt")

        with open(srt_path, "w", encoding="utf-8") as f: f.write(srt_content)

        return FileResponse(srt_path, media_type="text/plain", filename=srt_filename)

    finally:
        if os.path.exists(save_path): os.remove(save_path)

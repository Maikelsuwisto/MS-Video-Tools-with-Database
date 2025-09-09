import os, re, uuid, shutil
from faster_whisper import WhisperModel

model = None

def get_model():
    global model
    if model is None:
        print("Loading Whisper tiny model...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Model loaded successfully.")
    return model

def seconds_to_hms(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def split_segment_text_precise(text, start_time, end_time):
    sentences = re.split(r'([.!?])', text)
    sentences = [(sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")) for i in range(0, len(sentences), 2)]
    sentences = [s.strip() for s in sentences if s.strip()]
    total_chars = sum(len(s) for s in sentences)
    results, current_time = [], start_time

    for s in sentences:
        proportion = len(s) / total_chars if total_chars > 0 else 0
        duration = proportion * (end_time - start_time)
        results.append({"text": s, "start": current_time, "end": current_time + duration})
        current_time += duration

    return results

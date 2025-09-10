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

def split_srt_segments(text, start_time, end_time, max_chars=40, max_lines=2):
    """
    Split text into SRT-ready subtitle blocks with proper time allocation.
    """
    import textwrap
    # --- 1. Split by sentences ---
    sentences = re.split(r'([.!?])', text)
    sentences = [
        (sentences[i] + (sentences[i+1] if i+1 < len(sentences) else ""))
        for i in range(0, len(sentences), 2)
    ]
    sentences = [s.strip() for s in sentences if s.strip()]

    # --- 2. Allocate time proportionally per sentence ---
    total_chars = sum(len(s) for s in sentences)
    results, current_time = [], start_time

    for s in sentences:
        proportion = len(s) / total_chars if total_chars > 0 else 0
        duration = proportion * (end_time - start_time)
        sentence_end = current_time + duration

        # --- 3. Wrap into lines max 40 chars ---
        wrapped = textwrap.wrap(s, width=max_chars)

        # --- 4. Chunk into blocks (max 2 lines) ---
        for i in range(0, len(wrapped), max_lines):
            block_lines = wrapped[i:i+max_lines]
            block_text = "\n".join(block_lines)

            # Allocate proportional time for this chunk
            chunk_chars = sum(len(line) for line in block_lines)
            chunk_duration = duration * (chunk_chars / len(s))
            chunk_start, chunk_end = current_time, current_time + chunk_duration

            results.append({
                "text": block_text,
                "start": chunk_start,
                "end": chunk_end
            })

            current_time = chunk_end

    return results



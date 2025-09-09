import re

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
    sentences = [
        (sentences[i] + (sentences[i+1] if i+1 < len(sentences) else ""))
        for i in range(0, len(sentences), 2)
    ]
    sentences = [s.strip() for s in sentences if s.strip()]
    total_chars = sum(len(s) for s in sentences)
    results = []
    current_time = start_time

    for s in sentences:
        proportion = len(s) / total_chars if total_chars > 0 else 0
        duration = proportion * (end_time - start_time)
        results.append({
            "text": s,
            "start": current_time,
            "end": current_time + duration
        })
        current_time += duration

    return results

def split_sentences(text: str):
    parts = re.split(r'([.!?])', text)
    sentences = [
        (parts[i] + (parts[i+1] if i+1 < len(parts) else "")).strip()
        for i in range(0, len(parts), 2)
    ]
    return [s for s in sentences if s]

def wrap_text_to_two_lines(sentence: str, max_chars_per_line: int = 40):
    words = sentence.split()
    current_line = ""
    lines = []
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    if len(lines) > 2:
        lines = [lines[0], " ".join(lines[1:])]
    return lines

def generate_srt(segments, first_speech_time: float = 0.0, max_chars_per_line: int = 40):
    lines = []
    first_adjusted = False
    index = 1
    for seg in segments:
        start, end = seg.start, seg.end
        if not first_adjusted and first_speech_time > 0:
            start = first_speech_time
            first_adjusted = True
        sentences = split_sentences(seg.text.strip())
        total_chars = sum(len(s) for s in sentences)
        current_time = start
        for s in sentences:
            proportion = len(s) / total_chars if total_chars > 0 else 0
            duration = proportion * (end - start)
            s_start, s_end = current_time, current_time + duration
            current_time = s_end
            wrapped_lines = wrap_text_to_two_lines(s, max_chars_per_line)
            lines.append(str(index))
            lines.append(f"{format_srt_time(s_start)} --> {format_srt_time(s_end)}")
            lines.extend(wrapped_lines)
            lines.append("")
            index += 1
    return "\n".join(lines)

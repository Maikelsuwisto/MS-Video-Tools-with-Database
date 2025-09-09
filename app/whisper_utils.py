import os
import subprocess
import webrtcvad
from pydub import AudioSegment

model = None

def get_model():
    global model
    if model is None:
        print("Loading Whisper tiny model...")
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Model loaded successfully.")
    return model

ffmpeg_path = "ffmpeg"

def extract_audio_ffmpeg(video_path, audio_path="audio.wav"):
    cmd = [ffmpeg_path, '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
           '-ar', '16000', '-ac', '1', audio_path]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {process.stderr.decode()}")
    return audio_path

def detect_first_speech_offset_webrtcvad(audio_path, aggressiveness=3,
                                         min_speech_ms=1000, ignore_before_ms=1000):
    audio = AudioSegment.from_wav(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    raw_audio = audio.raw_data
    vad = webrtcvad.Vad(aggressiveness)
    frame_duration = 30
    frame_size = int(16000 * frame_duration / 1000) * 2
    frames = [raw_audio[i:i+frame_size] for i in range(0, len(raw_audio), frame_size)]
    speech_start_frame = None
    speech_frames_count = 0
    required_speech_frames = min_speech_ms // frame_duration
    ignore_before_frames = ignore_before_ms // frame_duration
    for i, frame in enumerate(frames):
        if len(frame) < frame_size:
            break
        if vad.is_speech(frame, sample_rate=16000):
            if speech_start_frame is None:
                speech_start_frame = i
            speech_frames_count += 1
        else:
            if speech_start_frame is not None and speech_frames_count >= required_speech_frames:
                if speech_start_frame >= ignore_before_frames:
                    return (speech_start_frame * frame_duration) / 1000.0
            speech_start_frame = None
            speech_frames_count = 0
    if speech_start_frame is not None and speech_frames_count >= required_speech_frames:
        if speech_start_frame >= ignore_before_frames:
            return (speech_start_frame * frame_duration) / 1000.0
    return 0.0

def detect_first_speech(video_path):
    audio_path = "temp.wav"
    try:
        audio_path = extract_audio_ffmpeg(video_path, audio_path)
        offset_sec = detect_first_speech_offset_webrtcvad(audio_path)
        return offset_sec
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

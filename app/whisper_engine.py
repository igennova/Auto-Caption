import whisper
import os

def transcribe_video(video_path: str, model_size: str = "base"):
    """
    Extracts audio (or acts on video path directly) and transcribes using Whisper.
    Returns standard SRT format string or list of dictionary segments.
    """
    model = whisper.load_model(model_size)
    
    result = model.transcribe(
        video_path,
        task="translate",
        initial_prompt="A Hinglish conversation in Roman script. For example: Main thik hu bro, tu kaisa hai?"
    )
    return result["segments"]

def segments_to_srt(segments) -> str:
    """ Converts whisper segments format to SRT text """
    def format_time(seconds):
        ms = int(seconds * 1000 % 1000)
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    srt_content = []
    for i, segment in enumerate(segments, start=1):
        start = format_time(segment['start'])
        end = format_time(segment['end'])
        text = segment['text'].strip()
        srt_content.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_content)

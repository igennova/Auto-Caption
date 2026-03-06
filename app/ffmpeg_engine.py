import subprocess
import os

def extract_audio(video_path: str, output_audio_path: str):
    """ Extract audio for faster transcription if needed. """
    command = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_audio_path
    ]
    subprocess.run(command, check=True)

def burn_subtitles(video_path: str, srt_path: str, output_video_path: str, font=None, size=None, color=None, margin_v=None, alignment=2):
    """ Burn subtitles using FFmpeg filters with optional styles. """
    
    style_params = []
    if font:
        style_params.append(f"FontName={font}")
    if size:
        style_params.append(f"FontSize={size}")
    if color:
        style_params.append(f"PrimaryColour={color}")
    if margin_v is not None:
        style_params.append(f"MarginV={margin_v}")
    if alignment is not None:
        style_params.append(f"Alignment={alignment}")
        
    filter_args = f"subtitles={srt_path}"
    if style_params:
        force_style = ",".join(style_params)
        filter_args += f":force_style='{force_style}'"

    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", filter_args,
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-c:a", "copy",
        output_video_path
    ]
    subprocess.run(command, check=True)

def preview_subtitles(video_path: str, srt_path: str, font=None, size=None, color=None, margin_v=None, alignment=2):
    """ Preview subtitles in real-time using ffplay. """
    style_params = []
    if font:
        style_params.append(f"FontName={font}")
    if size:
        style_params.append(f"FontSize={size}")
    if color:
        style_params.append(f"PrimaryColour={color}")
    if margin_v is not None:
        style_params.append(f"MarginV={margin_v}")
    if alignment is not None:
        style_params.append(f"Alignment={alignment}")
        
    filter_args = f"subtitles={srt_path}"
    if style_params:
        force_style = ",".join(style_params)
        filter_args += f":force_style='{force_style}'"

    command = [
        "ffplay", "-i", video_path,
        "-vf", filter_args,
        "-autoexit"
    ]
    subprocess.Popen(command)

def extract_thumbnail(video_path: str, output_image_path: str):
    """ Extract a single frame from the video to serve as a thumbnail. """
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", "00:00:01", "-frames:v", "1",
        "-vf", "scale=320:-1",
        output_image_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

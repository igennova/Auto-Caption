# Auto Caption MVP

A desktop app that auto-generates captions for your videos using OpenAI Whisper and burns them in using FFmpeg. Built with PyQt6.

## Demo

## What It Does

- Import any video (mp4, mkv, avi, mov)
- Auto-transcribe audio to text using Whisper AI
- Edit captions (text, timing) in a table
- Style captions — font, size, color, position
- Karaoke-style word highlighting
- Preview with captions before exporting
- Export final video with burned-in subtitles
- Save/export .SRT subtitle files

## Requirements

- Python 3.10+
- FFmpeg installed on your system

## How to Run Locally

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd auto_caption_mvp
```

### 2. Install FFmpeg (if not already installed)

**Mac:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

**Linux:**
```bash
sudo apt install ffmpeg
```

### 3. Create a virtual environment

```bash
python3 -m venv venv
```

### 4. Activate it

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the app

```bash
cd app
python main.py
```

The app window will open. Import a video, generate captions, edit them, and export!

## Project Structure

```
auto_caption_mvp/
├── app/
│   ├── main.py            # UI and app logic (PyQt6)
│   ├── whisper_engine.py   # Whisper transcription
│   ├── ffmpeg_engine.py    # FFmpeg video processing
│   └── srt_editor.py       # SRT parsing, saving, karaoke
├── requirements.txt
├── .gitignore
└── README.md
```

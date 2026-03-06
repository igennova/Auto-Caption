import re

def parse_srt(srt_content: str):
    """ Parse SRT text into a workable list of generic subtitle dicts. """
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.|\n)*?)(?=\n\n|$)', re.MULTILINE)
    matches = pattern.findall(srt_content)
    
    subtitles = []
    for match in matches:
        subtitles.append({
            "index": match[0],
            "start": match[1],
            "end": match[2],
            "text": match[3].strip()
        })
    return subtitles

def save_srt(subtitles_list, file_path: str):
    """ Save list of dicts back to an SRT file. """
    with open(file_path, 'w', encoding='utf-8') as f:
        for sub in subtitles_list:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")

def time_to_seconds(t_str):
    h, m, s_ms = t_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000

def seconds_to_time(seconds):
    ms = int(round(seconds * 1000)) % 1000
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def create_karaoke_srt(subtitles_list, file_path: str, highlight_color: str):
    """ Mathematically splits full sentences into word-by-word highlighted lines natively rendering in modern players/ffmpeg """
    karaoke_subs = []
    index = 1
    for sub in subtitles_list:
        text = sub['text']
        words = text.split()
        if not words:
            continue
            
        start_sec = time_to_seconds(sub['start'])
        end_sec = time_to_seconds(sub['end'])
        
        if end_sec <= start_sec:
            end_sec = start_sec + 0.5
            
        duration = end_sec - start_sec
        word_dur = duration / len(words)
        
        for i, target_word in enumerate(words):
            cur_start = start_sec + i * word_dur
            cur_end = cur_start + word_dur
            
            highlighted_words = []
            for j, w in enumerate(words):
                if j == i:
                    highlighted_words.append(f'<font color="{highlight_color}">{w}</font>')
                else:
                    highlighted_words.append(w)
            
            karaoke_subs.append({
                "index": str(index),
                "start": seconds_to_time(cur_start),
                "end": seconds_to_time(cur_end),
                "text": " ".join(highlighted_words)
            })
            index += 1
            
    save_srt(karaoke_subs, file_path)

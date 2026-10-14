import os
import sys
import json
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('outputs', exist_ok=True)
os.makedirs('outputs/temp_clips', exist_ok=True)

# 7 Shots configuration
shots = [
    {
        "id": 1,
        "slide": "assets/slides/slide1.png",
        "audio": "assets/tts_audio/shot1.mp3",
        "zoom": "min(zoom+0.0006,1.06)"
    },
    {
        "id": 2,
        "slide": "assets/slides/slide2.png",
        "audio": "assets/tts_audio/shot2.mp3",
        "zoom": "min(zoom+0.0004,1.05)"
    },
    {
        "id": 3,
        "slide": "assets/slides/slide3.png",
        "audio": "assets/tts_audio/shot3.mp3",
        "zoom": "min(zoom+0.0005,1.05)"
    },
    {
        "id": 4,
        "slide": "assets/slides/slide4.png",
        "audio": "assets/tts_audio/shot4.mp3",
        "zoom": "min(zoom+0.0003,1.04)"
    },
    {
        "id": 5,
        "slide": "assets/slides/slide5.png",
        "audio": "assets/tts_audio/shot5.mp3",
        "zoom": "min(zoom+0.0004,1.05)"
    },
    {
        "id": 6,
        "slide": "assets/slides/slide6.png",
        "audio": "assets/tts_audio/shot6.mp3",
        "zoom": "min(zoom+0.0003,1.03)"
    },
    {
        "id": 7,
        "slide": "assets/slides/slide7.png",
        "audio": "assets/tts_audio/shot7.mp3",
        "zoom": "min(zoom+0.0006,1.05)"
    }
]

print("=== Step 1: Measuring audio durations ===")
total_duration = 0.0
for s in shots:
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', s['audio']]
    res = subprocess.check_output(cmd)
    d = float(json.loads(res)['format']['duration'])
    s['duration'] = d
    total_duration += d
    print(f"Shot {s['id']}: {d:.2f}s")

print(f"Total Video Duration: {total_duration:.2f}s (~{int(total_duration)}s)")

print("\n=== Step 2: Rendering individual shots with Ken Burns motion ===")
concat_list_path = 'outputs/temp_clips/concat_list.txt'
with open(concat_list_path, 'w', encoding='utf-8') as f_list:
    for s in shots:
        clip_path = f"outputs/temp_clips/clip{s['id']}.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', s['slide'],
            '-i', s['audio'],
            '-vf', f"zoompan=z='{s['zoom']}':d=300:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '44100',
            '-ac', '2',
            '-shortest',
            clip_path
        ]
        print(f"Rendering Clip {s['id']} ({s['duration']:.2f}s)...")
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        f_list.write(f"file 'clip{s['id']}.mp4'\n")

print("\n=== Step 3: Concatenating all clips ===")
raw_video_path = 'outputs/temp_clips/raw_concatenated.mp4'
cmd_concat = [
    'ffmpeg', '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', concat_list_path,
    '-c', 'copy',
    raw_video_path
]
subprocess.check_call(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Concatenation complete!")

print("\n=== Step 4: Mixing background music with audio ducking & fading ===")
final_output = 'outputs/mangoblue_reels_45s.mp4'
bgm_path = 'assets/bgm_acoustic.wav'

# Audio filter explanation:
# [0:a] is voiceover track from raw video, normalized volume 1.15
# [1:a] is BGM track, looped or trimmed, volume 0.18, with gentle fade out at the end
fade_out_start = max(0.0, total_duration - 2.5)
filter_complex = (
    f"[0:a]volume=1.2[vo];"
    f"[1:a]volume=0.18,afade=t=out:st={fade_out_start:.2f}:d=2.5[bgm];"
    f"[vo][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
)

cmd_final = [
    'ffmpeg', '-y',
    '-i', raw_video_path,
    '-i', bgm_path,
    '-filter_complex', filter_complex,
    '-map', '0:v',
    '-map', '[aout]',
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-movflags', '+faststart',
    final_output
]
subprocess.check_call(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n=======================================================")
print(f"SUCCESS! Final Instagram Reel exported to:\n{os.path.abspath(final_output)}")
print("=======================================================")

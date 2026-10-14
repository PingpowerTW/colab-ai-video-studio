import os
import sys
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('outputs', exist_ok=True)

image_path = 'assets/golden_dragon.png'
audio_path = 'assets/audio/dragon_roar_wind.wav'
output_path = 'outputs/golden_dragon_cinematic.mp4'

print("=== Assembling Cinematic Golden Dragon Video with Sound ===")
print(f"Visual asset: {image_path}")
print(f"Soundtrack: {audio_path}")
print(f"Output: {output_path}")

# Filter graph explanation:
# 1. zoompan:
#    - Initial zoom slowly zooms into dragon's mouth: z='min(zoom+0.0008,1.20)'
#    - Shake effect during roar peak (frames 54 to 150, corresponding to 1.8s - 5.0s):
#      x jitter: + if(between(on,54,150),sin(on*3.5)*8,0)
#      y jitter: + if(between(on,54,150),cos(on*4.2)*6,0)
# 2. Lightning flash at t=1.8s (frame 54-58) and t=3.2s (frame 96-100) using curves / eq:
#    brightness bump when frame is between 54..58 or 96..100
# 3. Output 1920x1080 30fps H.264 High Profile

vf_filter = (
    "scale=2560:-1,"
    "zoompan="
    "z='min(zoom+0.0006,1.18)':"
    "x='(iw-iw/zoom)/2 + if(between(on,55,150),sin(on*3.7)*12,0)':"
    "y='(ih-ih/zoom)/2 + if(between(on,55,150),cos(on*4.3)*9,0)':"
    "d=240:s=1920x1080:fps=30,"
    "eq=brightness='if(between(n,55,58),0.35,if(between(n,95,98),0.25,0.0))':"
    "contrast='if(between(n,55,58),1.3,if(between(n,95,98),1.2,1.0))'"
)

cmd = [
    'ffmpeg', '-y',
    '-loop', '1',
    '-i', image_path,
    '-i', audio_path,
    '-vf', vf_filter,
    '-c:v', 'libx264',
    '-preset', 'slow',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '256k',
    '-t', '8.0',
    '-movflags', '+faststart',
    output_path
]

print("Executing FFmpeg encoding...")
subprocess.check_call(cmd)

print("\n=======================================================")
print(f"SUCCESS! Master cinematic video exported to:\n{os.path.abspath(output_path)}")
print("=======================================================")

import wave
import math
import struct
import random
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('assets/audio', exist_ok=True)

SAMPLE_RATE = 44100
DURATION = 8.0  # 8 seconds epic cinematic sequence
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

output_wav = 'assets/audio/dragon_roar_wind.wav'

print(f"Synthesizing {DURATION}s cinematic Dragon Roar & Gale Wind to {output_wav}...")

# Pre-generate noise buffers for wind and guttural rasp
random.seed(42)
white_noise = [random.uniform(-1.0, 1.0) for _ in range(NUM_SAMPLES)]

# Lowpass/Bandpass state variables
b_wind_lp = 0.0
b_wind_bp = 0.0
b_throat_lp = 0.0
b_rasp = 0.0

frames = bytearray()

for i in range(NUM_SAMPLES):
    t = i / SAMPLE_RATE
    
    # -------------------------------------------------------------
    # 1. Fierce Howling Wind & Atmosphere (狂風)
    # -------------------------------------------------------------
    # Wind gust velocity profile: swells from 0 to peak at 2.5s - 5.5s
    gust_intensity = 0.4 + 0.35 * math.sin(t * 0.8) + 0.25 * math.sin(t * 2.1)
    
    # Low rumble wind (Brownian filter)
    b_wind_lp += (white_noise[i] - b_wind_lp) * 0.04
    rumble = b_wind_lp * 1.8 * gust_intensity
    
    # Howling whistle (sweeping resonant filter around 400Hz - 900Hz)
    howl_freq = 450 + 250 * math.sin(t * 1.5) + 150 * math.sin(t * 3.7)
    howl_osc = math.sin(2 * math.pi * howl_freq * t) * (0.15 + 0.1 * math.sin(t * 2.8))
    
    wind_sound = (rumble * 0.6 + howl_osc * 0.4) * gust_intensity
    
    # -------------------------------------------------------------
    # 2. Thunder Crack & Sub-Bass Shockwave (雷鳴地動)
    # -------------------------------------------------------------
    # Thunder strike at t = 1.8s
    thunder = 0.0
    if t >= 1.8:
        td = t - 1.8
        th_env = math.exp(-td * 1.2)
        th_freq = 65 * math.exp(-td * 0.6)
        thunder = (0.5 * math.sin(2 * math.pi * th_freq * td) + 0.3 * (white_noise[i] * math.exp(-td * 2.5))) * th_env
    
    # -------------------------------------------------------------
    # 3. The Colossal Dragon Roar (巨龍咆哮)
    # -------------------------------------------------------------
    # Roar envelope starts inhaling/growling at t=1.2s, reaches massive climax at 2.5s-5.0s, dies down by 6.8s
    dragon_sound = 0.0
    if 1.0 <= t <= 7.0:
        rt = t - 1.0
        # Multi-stage roar envelope
        if rt < 1.0:
            # Stage 1: Inhale / Deep guttural pre-growl (1.0s - 2.0s)
            r_env = (rt / 1.0) ** 2 * 0.45
            base_pitch = 85 + 30 * rt
        elif rt < 3.8:
            # Stage 2: FULL ROAR CLIMAX (2.0s - 4.8s)
            peak_progress = (rt - 1.0) / 2.8
            r_env = 0.95 + 0.15 * math.sin(peak_progress * math.pi * 3.5)
            # Pitch starts high (145Hz) then lowers with immense power (95Hz)
            base_pitch = 145 - 45 * peak_progress
        else:
            # Stage 3: Decaying cavernous growl & echo (4.8s - 6.0s)
            decay_p = (rt - 3.8) / 2.2
            r_env = max(0.0, 0.95 * (1.0 - decay_p) ** 1.8)
            base_pitch = 90 - 30 * decay_p
            
        # Frequency Modulation (growl rasp)
        fm_mod = 35 * math.sin(2 * math.pi * 26 * rt)
        actual_freq = max(40.0, base_pitch + fm_mod)
        
        # Fundamental tone + heavy aggressive harmonics
        phase = 2 * math.pi * actual_freq * t
        h1 = math.sin(phase)
        h2 = 0.7 * math.sin(2 * phase)
        h3 = 0.5 * math.sin(3 * phase + 0.5)
        h4 = 0.35 * math.sin(4 * phase + 1.2)
        h5 = 0.25 * math.sin(5 * phase + 2.0)
        
        # Soft-clip distortion for ferocious organic beast growl
        raw_voice = (h1 + h2 + h3 + h4 + h5) * 0.6
        distorted_voice = math.tanh(raw_voice * 2.2)
        
        # Guttural throat rasp (noise modulated by pitch)
        rasp = white_noise[i] * (0.4 + 0.6 * math.sin(phase)) * 0.5
        
        dragon_sound = (distorted_voice * 0.75 + rasp * 0.35) * r_env
        
    # -------------------------------------------------------------
    # 4. Master Mix & Dynamics
    # -------------------------------------------------------------
    master_mix = wind_sound * 0.5 + thunder * 0.6 + dragon_sound * 0.85
    
    # Master limiter
    master_mix = math.tanh(master_mix * 1.1)
    
    # Stereo panning (dragon centered, wind wider, slight stereo motion)
    left_sample = master_mix + (rumble * 0.2) + (howl_osc * 0.15)
    right_sample = master_mix - (rumble * 0.15) - (howl_osc * 0.15)
    
    # Clamping & 16-bit PCM conversion
    left_int = int(max(-1.0, min(1.0, left_sample)) * 31000)
    right_int = int(max(-1.0, min(1.0, right_sample)) * 31000)
    
    frames += struct.pack('<hh', left_int, right_int)

with wave.open(output_wav, 'wb') as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(frames)

print(f"Generated {output_wav} successfully! ({len(frames)} bytes)")

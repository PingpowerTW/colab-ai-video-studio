import sys
from pathlib import Path

# Add minimax_h3 to sys.path
sys.path.insert(0, str(Path("minimax_h3/scripts").resolve()))
from runner import compose_ref2va_prompt

subject_definitions = (
    "<Subject 1>: The colossal oriental golden dragon from <Picture 1>, featuring intricate glistening golden scales, "
    "majestic antlers, flowing long whiskers, fierce glowing amber eyes, and powerful draconic jaws."
)

summary = (
    "A breathtaking cinematic sequence of the colossal golden dragon surging forward through a stormy cloud sea, "
    "opening its jaws wide, and roaring ferociously amidst roaring gale winds and rolling thunder."
)

retention_analysis = (
    "Preserve the golden dragon's regal Chinese mythical anatomy, glistening metallic gold scales, facial structure, "
    "and dark dramatic thundercloud ambiance depicted in <Picture 1>."
)

shots = [
    {
        "start_seconds": 0.0,
        "description": (
            "Cinematic fantasy masterpiece. The colossal golden dragon <Subject 1> from <Picture 1> undulates powerfully "
            "through turbulent dark storm clouds and vivid lightning flashes. Its golden scales gleam brilliantly as wind "
            "whips through its flowing whiskers. The camera pushes in dynamically as the dragon coils and lunges forward, "
            "opening its massive jaws wide to release a ferocious, deafening roar."
        )
    }
]

overall_soundscape = (
    "Violent howling gale winds, deep rumbling thunder, lightning crackles, and an ear-splitting, majestic dragon roar."
)

non_diegetic_music = "N/A"

prompt_text = compose_ref2va_prompt(
    subject_definitions=subject_definitions,
    summary=summary,
    retention_analysis=retention_analysis,
    shots=shots,
    overall_soundscape=overall_soundscape,
    non_diegetic_music=non_diegetic_music,
    image_count=1,
    duration_seconds=6.0,
)

Path("prompts").mkdir(parents=True, exist_ok=True)
output_prompt_file = Path("prompts/golden_dragon_h3.txt")
output_prompt_file.write_text(prompt_text, encoding="utf-8")

print(f"Ref2VA Prompt generated successfully at: {output_prompt_file}")
print("--- PROMPT PREVIEW ---")
print(prompt_text)

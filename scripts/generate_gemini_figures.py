"""
Generate conceptual project visuals with Gemini:
1) Hero illustration for README top section (also used as conceptual diagram)

Usage (PowerShell):
  $env:GEMINI_API_KEY="your_key"
  python scripts/generate_gemini_figures.py
"""

from __future__ import annotations

import os
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "figures"
HERO_PATH = OUT_DIR / "hero_top.jpg"
MODEL_CANDIDATES = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash",
]


def _extract_first_image_bytes(response: object) -> bytes:
    """Extract first inline image payload from Gemini response."""
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data and getattr(inline_data, "data", None):
                return inline_data.data
    raise RuntimeError("No image bytes found in Gemini response.")


def _generate_png(client: genai.Client, prompt: str, out_path: Path) -> None:
    last_error: Exception | None = None
    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                ),
            )
            image_bytes = _extract_first_image_bytes(response)
            out_path.write_bytes(image_bytes)
            print(f"Used model: {model_name}")
            return
        except Exception as exc:  # pragma: no cover
            last_error = exc
            continue
    raise RuntimeError(
        f"Failed to generate image with all model candidates: {MODEL_CANDIDATES}"
    ) from last_error


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY (or GOOGLE_API_KEY).")
        print("Set it, then rerun: python scripts/generate_gemini_figures.py")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=api_key)

    hero_prompt = (
        "Create a really cool cinematic conceptual hero illustration for an AI analytics research project. "
        "The image must be non-technical and emotionally clear, but strongly related to the project mission: "
        "transforming raw enterprise data into meaningful business questions and actionable insight. "
        "Visual narrative: left side shows overwhelming messy information fragments and disconnected data sources; "
        "middle shows a calm intelligent guide/compass-like light forming order; "
        "right side shows confident decision-making, clear insight cards, and forward movement. "
        "Mood: ambitious, intelligent, optimistic, premium. "
        "Style: high-end editorial illustration, rich depth, dramatic lighting, modern color harmony (deep blue, teal, warm amber), "
        "white-space-friendly for README, very polished, no watermark, no logos, no long text."
    )

    print("Generating hero image with Gemini...")
    _generate_png(client, hero_prompt, HERO_PATH)
    print(f"Saved: {HERO_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

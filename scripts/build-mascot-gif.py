#!/usr/bin/env python3
"""Monta o GIF transparente do README a partir de poses desenhadas separadamente.

Instalação: python -m pip install 'Pillow>=11,<13'
Execução: python scripts/build-mascot-gif.py [caminho-de-saida.gif]
Os PNGs fonte ficam em profile/assets/mascot-poses/ para que o loop seja editável.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
POSE_DIR = ROOT / "profile" / "assets" / "mascot-poses"
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "profile" / "assets" / "amber-mascot.gif"
SIZE = (360, 320)
SCALE = 0.25
BASELINE = 303
TRANSPARENT = 255
POSES = {
    "idle": "idle.png",
    "walk_a": "walk-left-a.png",
    "walk_b": "walk-left-b.png",
    "lift": "lift.png",
    "laptop_a": "laptop-a.png",
    "laptop_b": "laptop-b.png",
}


def load_pose(name: str) -> Image.Image:
    image = Image.open(POSE_DIR / POSES[name]).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value >= 70 else 0).getbbox()
    if bbox is None:
        raise ValueError(f"Pose sem pixels visíveis: {name}")
    cropped = image.crop(bbox)
    target = (round(cropped.width * SCALE), round(cropped.height * SCALE))
    return cropped.resize(target, Image.Resampling.LANCZOS)


def draw(pose: Image.Image, x: int = 0, bob: int = 0, mirrored: bool = False) -> Image.Image:
    sprite = ImageOps.mirror(pose) if mirrored else pose
    frame = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    position = ((SIZE[0] - sprite.width) // 2 + x, BASELINE - sprite.height + bob)
    frame.alpha_composite(sprite, position)
    return frame


def frames_for_loop(poses: dict[str, Image.Image]) -> list[Image.Image]:
    frames: list[Image.Image] = []

    # O loop conta uma história: parte, treina, volta, trabalha no notebook e retorna.
    frames.extend(draw(poses["idle"]) for _ in range(5))
    for step in range(14):
        x = round(-34 * (step + 1) / 14)
        name = "walk_a" if (step // 2) % 2 == 0 else "walk_b"
        frames.append(draw(poses[name], x=x, bob=-2 if name == "walk_a" else 0))
    frames.extend(draw(poses["lift"], x=-34, bob=-2 if i in (2, 3, 4) else 0) for i in range(7))

    for step in range(18):
        x = round(-34 + 68 * (step + 1) / 18)
        name = "walk_a" if (step // 2) % 2 == 0 else "walk_b"
        frames.append(draw(poses[name], x=x, bob=-2 if name == "walk_a" else 0, mirrored=True))
    for step in range(15):
        name = "laptop_b" if step in (4, 5, 11) else "laptop_a"
        frames.append(draw(poses[name], x=34))

    for step in range(13):
        x = round(34 * (1 - (step + 1) / 13))
        name = "walk_a" if (step // 2) % 2 == 0 else "walk_b"
        frames.append(draw(poses[name], x=x, bob=-2 if name == "walk_a" else 0))
    frames.extend(draw(poses["idle"]) for _ in range(5))
    return frames


def shared_palette(poses: dict[str, Image.Image]) -> Image.Image:
    sample = Image.new("RGB", (SIZE[0] * 3, SIZE[1] * 2), (0, 0, 0))
    for index, pose in enumerate(poses.values()):
        sample.paste(pose, ((index % 3) * SIZE[0], (index // 3) * SIZE[1]), pose)
    palette = sample.quantize(colors=255, method=Image.Quantize.FASTOCTREE)
    colors = palette.getpalette()
    colors[TRANSPARENT * 3 : TRANSPARENT * 3 + 3] = [255, 0, 255]
    palette.putpalette(colors)
    return palette


def gif_frame(frame: Image.Image, palette: Image.Image) -> Image.Image:
    indexed = frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
    alpha = frame.getchannel("A")
    indexed.paste(TRANSPARENT, mask=alpha.point(lambda value: 255 if value < 110 else 0))
    indexed.info["transparency"] = TRANSPARENT
    return indexed


def main() -> None:
    poses = {name: load_pose(name) for name in POSES}
    frames = frames_for_loop(poses)
    palette = shared_palette(poses)
    indexed = [gif_frame(frame, palette) for frame in frames]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=80,
        loop=0,
        disposal=2,
        transparency=TRANSPARENT,
        optimize=False,
    )
    print(f"{OUTPUT}: {len(indexed)} quadros, {len(indexed) * 80 / 1000:.2f}s, loop infinito")


if __name__ == "__main__":
    main()

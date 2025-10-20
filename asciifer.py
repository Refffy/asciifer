import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont


class ImageToASCII:
    def __init__(
        self,
        image_path: str,
        font_path: str | None = None,
        output_text_path: str | None = None,
        output_image_path: str | None = None,
        font_size: int | None = 6,
        use_braille: bool = False,
    ) -> None:
        self.image = Image.open(image_path).convert("RGB")
        self.output_text_path = output_text_path
        self.output_image_path = output_image_path
        self.use_braille = use_braille
        self.characters = self._get_charset()
        self.font = self._load_font(font_path, font_size if font_size is not None else 6)

    def _get_charset(self) -> str:
        return "⠁⠗⠃⠎⠉⠞⠙⠥⠑⠧⠋⠺⠛⠭⠓⠽⠊⠵⠚⠠⠅⠼⠇⠲⠍⠂⠝⠢⠕⠆⠏⠤⠟" if self.use_braille else ".,;!vlLFE$"

    def _load_font(
        self, font_path: str | None, font_size: int
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if font_path is not None and os.path.isfile(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except OSError:
                print(f"Couldn't open font {font_path}")

        fallback = ImageFont.load_default()
        return fallback

    def _get_brightness_array(self) -> np.ndarray:
        arr = np.asarray(self.image).astype(np.float32)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        brightness = np.sqrt(0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2) / 255.0
        return brightness

    def _char_cell(self) -> tuple[int, int]:
        sample = self.characters[-1]
        bbox = self.font.getbbox(sample)
        char_w = max(1, bbox[2] - bbox[0])
        char_h = max(1, bbox[3] - bbox[1])
        return char_w, char_h

    def convert_to_ascii_by_blocks(self) -> None:
        width, height = self.image.size
        char_w, char_h = self._char_cell()

        brightness = self._get_brightness_array()
        h_blocks = height // char_h
        w_blocks = width // char_w

        brightness = brightness[: h_blocks * char_h, : w_blocks * char_w]

        brightness_blocks = brightness.reshape(h_blocks, char_h, w_blocks, char_w)
        avg_brightness = brightness_blocks.mean(axis=(1, 3))

        idx = (avg_brightness * (len(self.characters) - 1)).astype(np.int32)
        ascii_chars = np.array(list(self.characters))[idx]

        ascii_lines = ["".join(row) for row in ascii_chars]

        if self.output_text_path:
            with open(self.output_text_path, "w", encoding="utf-8") as f:
                f.write("\n".join(ascii_lines))

        if self.output_image_path:
            self._render_colored_ascii(ascii_lines, char_w, char_h)

        if not self.output_text_path and not self.output_image_path:
            print("\n".join(ascii_lines))

    def _render_colored_ascii(self, ascii_lines: list[str], char_w: int, char_h: int) -> None:
        cols = len(ascii_lines[0])
        rows = len(ascii_lines)
        resized_img = self.image.resize((cols, rows), Image.LANCZOS)
        resized_array = np.asarray(resized_img)

        output_w = char_w * cols
        output_h = char_h * rows
        output_img = Image.new("RGB", (output_w, output_h), color=(0, 0, 0))
        draw = ImageDraw.Draw(output_img)

        for y, line in enumerate(ascii_lines):
            for x, ch in enumerate(line):
                color = tuple(resized_array[y, x])
                draw.text((x * char_w, y * char_h), ch, font=self.font, fill=color)

        output_img = output_img.resize(self.image.size, Image.LANCZOS)
        output_img.save(self.output_image_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    parser.add_argument("input_image", help="Path to the input image file")

    parser.add_argument("--output-text", default=None, help="Path to save ASCII as text")
    parser.add_argument("--output-image", default=None, help="Path to save ASCII as an image")

    parser.add_argument("--font", default=None, help="Path to a .ttf/.otf font file (optional)")
    parser.add_argument("--font-size", type=int, default=6, help="Font size (default: 6)")
    parser.add_argument("--use-braille", action="store_true", help="Use Braille Unicode characters")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    converter = ImageToASCII(
        image_path=args.input_image,
        font_path=args.font,
        output_text_path=args.output_text,
        output_image_path=args.output_image,
        font_size=args.font_size,
        use_braille=args.use_braille,
    )
    converter.convert_to_ascii_by_blocks()


if __name__ == "__main__":
    main()

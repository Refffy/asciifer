import os
import sys
import argparse

import math
from PIL import Image, ImageDraw, ImageFont


class ImageToASCII:
    def __init__(
        self,
        image_path: str,
        font_path: str | None,
        output_text_path: str | None,
        output_image_path: str | None,
        font_size: int,
        use_braille: bool = False,
    ) -> None:
        self.image = Image.open(image_path).convert('RGB').resize((850, 850))
        self.output_text_path = output_text_path
        self.output_image_path = output_image_path
        self.font_size = font_size
        self.use_braille = use_braille
        self.characters = self._get_charset()

        if font_path is None or not os.path.isfile(font_path):
            print(f"Error: Font file not found: {font_path}")
            sys.exit(1)

        self.font = ImageFont.truetype(font_path, font_size)

    def _get_charset(self) -> str:
        return "⠁⠗⠃⠎⠉⠞⠙⠥⠑⠧⠋⠺⠛⠭⠓⠽⠊⠵⠚⠠⠅⠼⠇⠲⠍⠂⠝⠢⠕⠆⠏⠤⠟" if self.use_braille else ".,;!vlLFE$"

    def _get_brightness(self, x: int, y: int) -> float:
        r, g, b = self.image.getpixel((x, y))
        return math.sqrt(0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2) / 255

    def convert_to_ascii_by_blocks(self) -> None:
        width, height = self.image.size
        bbox = self.font.getbbox(self.characters[-1])
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]

        cols = width // char_w
        rows = height // char_h

        ascii_lines = []

        for y in range(rows):
            line = ""
            for x in range(cols):
                brightness_sum = 0.0
                for i in range(char_w):
                    for j in range(char_h):
                        px = x * char_w + i
                        py = y * char_h + j
                        if px < width and py < height:
                            brightness_sum += self._get_brightness(px, py)
                avg_brightness = brightness_sum / (char_w * char_h)
                char_index = int(avg_brightness * (len(self.characters) - 1))
                line += self.characters[char_index]
            ascii_lines.append(line)

        if self.output_text_path:
            with open(self.output_text_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(ascii_lines))

        if self.output_image_path:
            self._render_colored_ascii(ascii_lines, char_w, char_h)

        if not self.output_text_path and not self.output_image_path:
            print('\n'.join(ascii_lines))

    def _render_colored_ascii(self, ascii_lines: list[str], char_w: int, char_h: int) -> None:
        cols = len(ascii_lines[0])
        rows = len(ascii_lines)
        resized_img = self.image.resize((cols, rows), Image.LANCZOS)

        output_width = char_w * cols
        output_height = char_h * rows
        output_img = Image.new('RGB', (output_width, output_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(output_img)

        for y, line in enumerate(ascii_lines):
            for x, char in enumerate(line):
                color = resized_img.getpixel((x, y))
                draw.text((x * char_w, y * char_h), char, font=self.font, fill=color)

        output_img = output_img.resize(self.image.size, Image.LANCZOS)
        output_img.save(self.output_image_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert an image to ASCII art.")
    parser.add_argument("input_image", help="Path to the input image file")
    parser.add_argument("--output-text", help="Path to save ASCII as text", default=None)
    parser.add_argument("--output-image", help="Path to save ASCII as an image", default=None)
    parser.add_argument("--font-size", type=int, default=12, help="Font size (default-12)")
    parser.add_argument("--use-braille", action="store_true", help="Use Braille Unicode characters")
    parser.add_argument("--font", type=str, default="fonts/FiraCode-Bold.ttf", help="Path to a .ttf font file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    converter = ImageToASCII(
        image_path=args.input_image,
        output_text_path=args.output_text,
        output_image_path=args.output_image,
        font_size=args.font_size,
        use_braille=args.use_braille,
        font_path=args.font
    )
    converter.convert_to_ascii_by_blocks()


if __name__ == "__main__":
    main()

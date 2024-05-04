"""This module contains various tools for working with images and PDFs."""

from io import BytesIO

import pandas as pd
import weasyprint as wsp
from aiogram import types
from pdf2image import convert_from_bytes
from PIL import Image, ImageChops


def trim(src):
    """Trim the image."""

    background = src.getpixel((0, 0))
    border = Image.new(src.mode, src.size, background)
    diff = ImageChops.difference(src, border)
    bbox = diff.getbbox()
    img = src.crop(bbox) if bbox else src

    return img


def table(data, columns, caption: str = None, name: str = None):
    """Generate a table from the data."""

    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    df.index += 1

    css_text = (
        "@page { size: 800px 715px; padding: 0px; margin: 0px; }\n"
        "h4 {text-align: start;}\n"
        "table, td, tr, th { border: 1px solid black; }\n"
        "th { padding: 4px 8px; background-color: lightgray; }\n"
        "td { padding: 4px 8px; }\n"
        "th, td {text-align: center; }\n"
    )

    if "Game" in columns:
        css_text += (
            f"td:nth-child({columns.index('Game') + 2}) {{ text-align: left; }}\n"
        )

    # Generate CSS styles
    css = wsp.CSS(string=css_text)
    # Generate HTML with CSS
    html_string = df.to_html()
    if name is not None:
        html_string = f'<h4>{name}</h4>\n' + html_string
    html = wsp.HTML(string=html_string)
    pages = convert_from_bytes(html.write_pdf(stylesheets=[css]), dpi=100)

    media = []
    for i, page in enumerate(pages):
        trimmed = trim(page)
        img = BytesIO()
        trimmed.save(img, "PNG")
        img.seek(0)

        page = types.InputMediaPhoto(
                type="photo",
                media=types.BufferedInputFile(img.read(), filename=f"{i}.png")
        )
        if i == 0:
            page.caption = caption

        media.append(page)

    return media

import weasyprint as wsp
import pandas as pd

from aiogram import types
from PIL import ImageChops, Image
from io import BytesIO
from pdf2image import convert_from_bytes


def trim(src):
    background = src.getpixel((0, 0))
    border = Image.new(src.mode, src.size, background)
    diff = ImageChops.difference(src, border)
    bbox = diff.getbbox()
    img = src.crop(bbox) if bbox else src

    return img


def table(data, columns, caption: str = None):
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    df.index += 1

    css_text = ("@page { size: 800px 715px; padding: 0px; margin: 0px; }\n"
                "table, td, tr, th { border: 1px solid black; }\n"
                "th { padding: 4px 8px; background-color: lightgray; }\n"
                "td { padding: 4px 8px; }\n")

    # Apply styles for each column
    for i, column in enumerate(df.columns):
        match column:
            case 'Game':
                css_text += f'th:nth-child({i + 1}) {{ text-align: center; }}\n'  # Header
                css_text += f'td:nth-child({i + 1}) {{ text-align: left; }}\n'  # Content
                continue
            case _:
                css_text += f'th:nth-child({i + 1}) {{ text-align: center; }}\n'  # Header
                css_text += f'td:nth-child({i + 1}) {{ text-align: center; }}\n'  # Content
                continue

    # Generate CSS styles
    css = wsp.CSS(string=css_text)
    # Generate HTML with CSS
    html = wsp.HTML(string=df.to_html())
    pages = convert_from_bytes(html.write_pdf(stylesheets=[css]), dpi=100)

    media = []
    for i, page in enumerate(pages):
        trimmed = trim(page)
        img = BytesIO()
        trimmed.save(img, 'PNG')
        img.seek(0)

        if i == 0:
            page = types.InputMediaPhoto(type='photo', media=types.BufferedInputFile(img.read(), filename="i.png"),
                                         caption=caption)
        else:
            page = types.InputMediaPhoto(type='photo', media=types.BufferedInputFile(img.read(), filename="i.png"))
        media.append(page)

    return media

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
    df = pd.DataFrame(data, columns=columns)

    df.index += 1

    css = wsp.CSS(string='''
                    @page { size: 800px 715px; padding: 0px; margin: 0px; }
                    table, td, tr, th { border: 1px solid black; }
                    td, th { padding: 4px 8px; }
    ''')
    html = wsp.HTML(string=df.to_html())
    pages = convert_from_bytes(html.write_pdf(stylesheets=[css]), dpi=100)

    media = types.MediaGroup()
    for i, page in enumerate(pages):
        trimmed = trim(page)
        img = BytesIO()
        trimmed.save(img, 'PNG')
        img.seek(0)
        if i == 0 and caption is not None:
            media.attach_photo(img, caption)
        else:
            media.attach_photo(img)

    return media

"""
QR code generation service.

Generates a QR code image for a guest check-in URL and saves it to
MEDIA_ROOT/qr_codes/<token>.png.
"""

import io
import os
import re
from typing import Optional
from urllib.parse import urlencode
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps
from django.conf import settings
from django.core.files.base import ContentFile

QR_CODES_UPLOAD_PATH = "qr_codes/"
LOGO_PADDING = 6
LOGO_SIZE_RATIO = 0.22
TEXT_PADDING = 16
TEXT_LINE_SPACING = 6
DEFAULT_QR_COLOR = "#0f172a"


def generate_qr_code(guest) -> str:
    """
    Generate a QR code for *guest* and persist it to the guest's
    qr_code_image field.

    Returns the relative file path (relative to MEDIA_ROOT).
    """
    checkin_url = _build_checkin_url(guest)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(checkin_url)
    qr.make(fit=True)

    fill_color = _get_event_color(guest.event)
    img = qr.make_image(fill_color=fill_color, back_color="white").convert("RGBA")
    img = _overlay_logo(img, guest.event, fill_color)
    img = _add_caption(img, guest)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{QR_CODES_UPLOAD_PATH}{guest.unique_token}.png"
    guest.qr_code_image.save(filename, ContentFile(buffer.read()), save=True)

    return filename


def _build_checkin_url(guest) -> str:
    base = settings.CHECKIN_DOMAIN.rstrip("/")
    query = urlencode({"token": str(guest.unique_token)})
    return f"{base}/checkin/?{query}"


def _get_event_color(event) -> str:
    value = getattr(event, "qr_color", "") or ""
    if _is_hex_color(value):
        return value.lower()
    if _is_hex_color(f"#{value}"):
        return f"#{value}".lower()
    return DEFAULT_QR_COLOR


def _is_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})", value or ""))


def _event_initials(event) -> str:
    parts = [part for part in str(event.name).strip().split() if part]
    if not parts:
        return "EV"
    initials = "".join(part[0] for part in parts[:2]).upper()
    return initials or "EV"


def _overlay_logo(img: Image.Image, event, fill_color: str) -> Image.Image:
    width, height = img.size
    logo_size = int(min(width, height) * LOGO_SIZE_RATIO)
    if logo_size <= 0:
        return img

    logo = _load_event_logo(event, logo_size)
    if logo is None:
        logo = _build_initials_logo(event, logo_size, fill_color)

    if logo is None:
        return img

    logo = logo.convert("RGBA")
    logo = ImageOps.fit(logo, (logo_size, logo_size), centering=(0.5, 0.5))

    background = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 255))
    bg_draw = ImageDraw.Draw(background)
    bg_draw.ellipse((0, 0, logo_size, logo_size), fill=(255, 255, 255, 255))

    background.paste(logo, (0, 0), mask=logo)

    pos = ((width - logo_size) // 2, (height - logo_size) // 2)
    img.paste(background, pos, mask=background)
    return img


def _load_event_logo(event, logo_size: int) -> Optional[Image.Image]:
    logo_field = getattr(event, "logo", None)
    if not logo_field:
        return None
    try:
        logo_path = logo_field.path
    except (ValueError, AttributeError):
        return None
    if not logo_path or not os.path.exists(logo_path):
        return None
    try:
        with Image.open(logo_path) as logo:
            return logo.copy()
    except (OSError, ValueError):
        return None


def _build_initials_logo(event, logo_size: int, fill_color: str) -> Optional[Image.Image]:
    initials = _event_initials(event)
    if not initials:
        return None

    logo = Image.new("RGBA", (logo_size, logo_size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((0, 0, logo_size, logo_size), outline=fill_color, width=3)

    font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (logo_size - text_width) // 2
    text_y = (logo_size - text_height) // 2
    draw.text((text_x, text_y), initials, fill=fill_color, font=font)
    return logo


def _add_caption(img: Image.Image, guest) -> Image.Image:
    event_name = str(guest.event.name).strip()
    subtitle = str(getattr(guest.event, "qr_caption", "") or "").strip()
    lines = [event_name] if event_name else []
    if subtitle:
        lines.append(subtitle)
    if not lines:
        lines = ["Scan to check in"]

    font_base = ImageFont.load_default()
    font_title = font_base.font_variant(size=18)
    font_sub = font_base.font_variant(size=14)
    fonts = [font_title, font_sub][: len(lines)]

    line_heights = []
    line_widths = []
    draw = ImageDraw.Draw(img)
    for line, font in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    text_height = sum(line_heights) + TEXT_LINE_SPACING * (len(lines) - 1)
    text_area_height = text_height + TEXT_PADDING * 2

    new_img = Image.new("RGBA", (img.width, img.height + text_area_height), (255, 255, 255, 255))
    new_img.paste(img, (0, 0))

    text_draw = ImageDraw.Draw(new_img)
    current_y = img.height + TEXT_PADDING
    for idx, (line, font) in enumerate(zip(lines, fonts)):
        line_width = line_widths[idx]
        x = (img.width - line_width) // 2
        fill = _get_event_color(guest.event) if idx == 0 else "#475569"
        text_draw.text((x, current_y), line, fill=fill, font=font)
        current_y += line_heights[idx] + TEXT_LINE_SPACING

    return new_img

"""
QR code generation service.

Generates a QR code image for a guest check-in URL and saves it to
MEDIA_ROOT/qr_codes/<token>.png.
"""

import io
import qrcode
from django.conf import settings
from django.core.files.base import ContentFile

QR_CODES_UPLOAD_PATH = "qr_codes/"


def generate_qr_code(guest) -> str:
    """
    Generate a QR code for *guest* and persist it to the guest's
    qr_code_image field.

    Returns the relative file path (relative to MEDIA_ROOT).
    """
    checkin_url = f"{settings.CHECKIN_DOMAIN}/api/checkin/{guest.unique_token}/"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(checkin_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{QR_CODES_UPLOAD_PATH}{guest.unique_token}.png"
    guest.qr_code_image.save(filename, ContentFile(buffer.read()), save=True)

    return filename

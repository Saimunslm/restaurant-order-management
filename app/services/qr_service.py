import qrcode
import qrcode.image.svg
import io
import base64
from app.extensions import db
from app.models.table import Table


def generate_qr_token():
    import uuid
    return uuid.uuid4().hex


def create_table_with_qr(table_number):
    qr_token = generate_qr_token()
    table = Table(table_number=table_number, qr_token=qr_token)
    db.session.add(table)
    db.session.commit()
    return table


def get_qr_image_base64(qr_token, base_url=""):
    url = f"{base_url}/scan/{qr_token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    factory = qrcode.image.svg.SvgImage
    img = qr.make_image(image_factory=factory)
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def regenerate_qr_token(table_id):
    table = Table.query.get_or_404(table_id)
    table.qr_token = generate_qr_token()
    db.session.commit()
    return table

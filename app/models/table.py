import uuid
from app.extensions import db


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, unique=True, nullable=False)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    waiter_called = db.Column(db.Boolean, default=False)

    # Reservation layout fields
    capacity = db.Column(db.Integer, default=4)
    shape = db.Column(db.String(20), default="round")  # round, square, rectangle
    pos_x = db.Column(db.Float, default=50.0)  # percentage 0-100
    pos_y = db.Column(db.Float, default=50.0)  # percentage 0-100
    color = db.Column(db.String(20), default="#10B981")  # hex color
    width = db.Column(db.Float, default=80.0)  # pixel width for visual
    height = db.Column(db.Float, default=80.0)  # pixel height for visual

    orders = db.relationship("Order", backref="table", lazy="dynamic")
    reservations = db.relationship("Reservation", backref="table", lazy="dynamic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex

    def __repr__(self):
        return f"<Table {self.table_number}>"

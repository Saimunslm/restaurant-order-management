import uuid
from datetime import datetime
from app.extensions import db


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), default="")
    guests = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=True)
    table_number = db.Column(db.Integer, nullable=True)  # keep for backward compat
    special_requests = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    STATUSES = ["pending", "confirmed", "cancelled", "completed"]

    def __repr__(self):
        return f"<Reservation {self.customer_name} - {self.date}>"

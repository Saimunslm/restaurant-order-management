import uuid
from app.extensions import db


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, unique=True, nullable=False)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    waiter_called = db.Column(db.Boolean, default=False)

    orders = db.relationship("Order", backref="table", lazy="dynamic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex

    def __repr__(self):
        return f"<Table {self.table_number}>"

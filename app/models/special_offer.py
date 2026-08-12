from datetime import datetime
from app.extensions import db


class SpecialOffer(db.Model):
    __tablename__ = "special_offers"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True)
    offer_price = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    @property
    def is_valid(self):
        now = datetime.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def __repr__(self):
        return f"<SpecialOffer {self.product_id} -> {self.offer_price}>"

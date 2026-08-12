from datetime import datetime
from app.extensions import db


class ComboOffer(db.Model):
    __tablename__ = "combo_offers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    combo_price = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500), default="")

    items = db.relationship("ComboItem", backref="combo", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def original_total(self):
        return sum(item.product.price * item.quantity for item in self.items)

    @property
    def savings(self):
        return self.original_total - self.combo_price

    @property
    def is_valid(self):
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date

    def __repr__(self):
        return f"<ComboOffer {self.name}>"


class ComboItem(db.Model):
    __tablename__ = "combo_items"

    id = db.Column(db.Integer, primary_key=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combo_offers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product", backref="combo_items")

    def __repr__(self):
        return f"<ComboItem {self.product.name} x{self.quantity}>"

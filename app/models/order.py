import uuid
from datetime import datetime
from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=False)
    session_token = db.Column(db.String(128), nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="received"
    )  # received, preparing, served, completed, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    STATUSES = ["received", "preparing", "served", "completed", "cancelled"]

    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items)
        return self.total_amount

    def __repr__(self):
        return f"<Order {self.id[:8]}...>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, default="")

    product = db.relationship("Product", backref="order_items")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __repr__(self):
        return f"<OrderItem {self.product.name} x{self.quantity}>"

from datetime import datetime
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.special_offer import SpecialOffer
from app.models.combo_offer import ComboOffer


def create_order(table_id, session_token, items_data, combos_data=None):
    order = Order(table_id=table_id, session_token=session_token, status="received")
    db.session.add(order)
    db.session.flush()

    for item_data in items_data:
        product = Product.query.get(item_data["product_id"])
        if not product or not product.is_available:
            continue

        price = product.price
        if product.special_offer and product.special_offer.is_valid:
            price = product.special_offer.offer_price

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data.get("quantity", 1),
            unit_price=price,
            notes=item_data.get("notes", ""),
        )
        db.session.add(order_item)

    for combo_data in combos_data or []:
        combo = ComboOffer.query.get(combo_data.get("combo_id"))
        if not combo or not combo.is_valid:
            continue
        combo_qty = combo_data.get("quantity", 1)
        lines_added = False
        for combo_item in combo.items:
            product = combo_item.product
            if not product or not product.is_available:
                continue
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=combo_item.quantity * combo_qty,
                unit_price=product.price,
                notes="",
            )
            db.session.add(order_item)
            lines_added = True
        savings = (combo.original_total - combo.combo_price) * combo_qty
        if lines_added and savings > 0 and combo.items:
            first_product = combo.items[0].product
            discount_item = OrderItem(
                order_id=order.id,
                product_id=first_product.id,
                quantity=1,
                unit_price=-savings,
                notes=f"Combo discount ({combo.name})",
            )
            db.session.add(discount_item)

    order.calculate_total()
    db.session.commit()
    return order


def update_order_status(order_id, new_status):
    order = Order.query.get_or_404(order_id)
    if new_status in Order.STATUSES:
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
    return order


def get_active_orders():
    return Order.query.filter(
        Order.status.in_(["received", "preparing"])
    ).order_by(Order.created_at.desc()).all()


def get_order_with_valid_session(order_id, session_token):
    order = Order.query.get_or_404(order_id)
    if order.session_token != session_token:
        return None
    return order

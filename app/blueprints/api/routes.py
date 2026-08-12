from flask import Blueprint, jsonify, request, session
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order
from app.models.table import Table
from app.services.order_service import create_order, update_order_status, get_active_orders
from app.services.offer_service import get_active_offers, check_and_expire_offers
from app.models.combo_offer import ComboOffer
from app.blueprints.customer.decorators import table_session_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/categories")
def get_categories():
    categories = Category.query.filter_by(status=True).order_by(Category.display_order).all()
    return jsonify([{"id": c.id, "name": c.name} for c in categories])


@api_bp.route("/products")
def get_products():
    category_id = request.args.get("category_id")
    query = Product.query.filter_by(is_available=True)
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    products = query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category_id": p.category_id,
            "image_url": p.image_url,
        }
        for p in products
    ])


@api_bp.route("/products/<int:product_id>")
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    offer = product.special_offer if product.special_offer and product.special_offer.is_valid else None
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "offer_price": offer.offer_price if offer else None,
        "category_id": product.category_id,
        "image_url": product.image_url,
    })


@api_bp.route("/offers")
def get_offers():
    check_and_expire_offers()
    offers = get_active_offers()
    return jsonify([
        {
            "id": o.id,
            "product_id": o.product_id,
            "product_name": o.product.name,
            "original_price": o.product.price,
            "offer_price": o.offer_price,
            "end_date": o.end_date.isoformat(),
        }
        for o in offers
    ])


@api_bp.route("/combos")
def get_combos():
    from datetime import datetime
    now = datetime.now()
    combos = ComboOffer.query.filter(
        ComboOffer.is_active == True,
        ComboOffer.start_date <= now,
        ComboOffer.end_date >= now,
    ).all()
    result = []
    for combo in combos:
        items = [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.product.price,
            }
            for item in combo.items
        ]
        result.append({
            "id": combo.id,
            "name": combo.name,
            "description": combo.description,
            "combo_price": combo.combo_price,
            "original_total": combo.original_total,
            "savings": combo.savings,
            "image_url": combo.image_url,
            "items": items,
            "end_date": combo.end_date.isoformat(),
        })
    return jsonify(result)


@api_bp.route("/orders", methods=["POST"])
@table_session_required
def submit_order():
    from flask import g
    data = request.get_json()
    items = data.get("items", [])
    combos = data.get("combos", [])

    if not items and not combos:
        return jsonify({"error": "No items in order"}), 400

    order = create_order(
        table_id=g.current_table.id,
        session_token=session.get("qr_token"),
        items_data=items,
        combos_data=combos,
    )

    return jsonify({
        "order_id": order.id,
        "total": order.total_amount,
        "status": order.status,
    }), 201


@api_bp.route("/orders/<order_id>/status")
@table_session_required
def get_order_status(order_id):
    from flask import g
    order = Order.query.get_or_404(order_id)
    if order.table_id != g.current_table.id:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({
        "order_id": order.id,
        "status": order.status,
        "total": order.total_amount,
        "created_at": order.created_at.isoformat(),
    })


@api_bp.route("/tables/<int:table_id>/call-waiter", methods=["POST"])
@table_session_required
def call_waiter(table_id):
    from flask import g
    if g.current_table.id != table_id:
        return jsonify({"error": "Forbidden"}), 403

    from app.extensions import db
    g.current_table.waiter_called = True
    db.session.commit()
    return jsonify({"success": True, "message": "Waiter notified"})


@api_bp.route("/kitchen/orders")
def kitchen_orders():
    check_and_expire_offers()
    orders = get_active_orders()
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "table_number": order.table.table_number,
            "status": order.status,
            "total": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "notes": item.notes,
                }
                for item in order.items
            ],
        })
    return jsonify(result)


@api_bp.route("/kitchen/orders/<order_id>/status", methods=["PATCH"])
def update_kitchen_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Status required"}), 400

    order = update_order_status(order_id, new_status)
    return jsonify({
        "order_id": order.id,
        "status": order.status,
    })


@api_bp.route("/kitchen/waiter-requests")
def waiter_requests():
    tables = Table.query.filter_by(waiter_called=True, is_active=True).all()
    return jsonify([
        {"table_id": t.id, "table_number": t.table_number}
        for t in tables
    ])


@api_bp.route("/kitchen/waiter-requests/<int:table_id>/clear", methods=["POST"])
def clear_waiter_request(table_id):
    from app.extensions import db
    table = Table.query.get_or_404(table_id)
    table.waiter_called = False
    db.session.commit()
    return jsonify({"success": True})

from flask import Blueprint, render_template, session, redirect, url_for, abort, g
from app.models.table import Table
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order
from app.services.offer_service import get_active_offers
from app.blueprints.customer.decorators import table_session_required

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/public-menu")
def public_menu():
    categories = Category.query.filter_by(status=True).order_by(Category.display_order).all()
    products = Product.query.filter_by(is_available=True).all()
    offers = get_active_offers()
    offer_map = {o.product_id: o for o in offers}

    return render_template(
        "customer/public_menu.html",
        categories=categories,
        products=products,
        offer_map=offer_map,
    )


@customer_bp.route("/reserve-table")
def reserve_table():
    return render_template("customer/reserve_table.html")


@customer_bp.route("/scan/<qr_token>")
def scan(qr_token):
    table = Table.query.filter_by(qr_token=qr_token, is_active=True).first_or_404()

    session["table_id"] = table.id
    session["qr_token"] = table.qr_token
    session.permanent = True

    return redirect(url_for("customer.menu"))


@customer_bp.route("/menu")
@table_session_required
def menu():
    table = g.current_table
    categories = Category.query.filter_by(status=True).order_by(Category.display_order).all()
    products = Product.query.filter_by(is_available=True).all()
    offers = get_active_offers()

    offer_map = {o.product_id: o for o in offers}

    return render_template(
        "customer/menu.html",
        table=table,
        categories=categories,
        products=products,
        offer_map=offer_map,
    )


@customer_bp.route("/order/<order_id>")
@table_session_required
def order_tracking(order_id):
    order = Order.query.get_or_404(order_id)
    if order.table_id != g.current_table.id:
        abort(403)
    if order.session_token != session.get("qr_token"):
        abort(403)

    return render_template("customer/order_tracking.html", order=order, table=g.current_table)


@customer_bp.route("/call-waiter", methods=["POST"])
@table_session_required
def call_waiter():
    from app.extensions import db
    g.current_table.waiter_called = True
    db.session.commit()
    return {"success": True, "message": "Waiter has been notified"}

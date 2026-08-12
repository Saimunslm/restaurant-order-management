import os
import uuid
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.category import Category
from app.models.product import Product
from app.models.table import Table
from app.models.order import Order
from app.models.special_offer import SpecialOffer
from app.models.combo_offer import ComboOffer, ComboItem
from app.models.staff_user import StaffUser
from app.blueprints.admin.forms import LoginForm, CategoryForm, ProductForm, TableForm, OfferForm, ComboOfferForm
from app.services.qr_service import create_table_with_qr, get_qr_image_base64, regenerate_qr_token
from app.services.offer_service import create_offer, deactivate_offer


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def save_uploaded_image(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        return filename
    return None


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = StaffUser.query.filter_by(email=form.email.data, role="admin").first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials", "error")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/tables/<int:id>/dismiss-waiter", methods=["POST"])
@login_required
@admin_required
def dismiss_waiter(id):
    table = Table.query.get_or_404(id)
    table.waiter_called = False
    db.session.commit()
    flash(f"Waiter call dismissed for Table {table.table_number}", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/orders/<order_id>/bill")
@login_required
@admin_required
def bill(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/bill.html", order=order)


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    active_orders = Order.query.filter(
        Order.status.in_(["received", "preparing"])
    ).count()
    total_tables = Table.query.filter_by(is_active=True).count()
    waiter_requests = Table.query.filter_by(waiter_called=True, is_active=True).count()
    called_tables = Table.query.filter_by(waiter_called=True, is_active=True).all()
    recent_orders = Order.query.filter(
        Order.status.in_(["received", "preparing", "served"])
    ).order_by(Order.created_at.desc()).limit(10).all()
    return render_template(
        "admin/dashboard.html",
        active_orders=active_orders,
        total_tables=total_tables,
        waiter_requests=waiter_requests,
        called_tables=called_tables,
        recent_orders=recent_orders,
    )


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, display_order=form.display_order.data or 0)
        db.session.add(category)
        db.session.commit()
        flash("Category added", "success")
        return redirect(url_for("admin.categories"))

    categories = Category.query.order_by(Category.display_order).all()
    return render_template("admin/categories.html", categories=categories, form=form)


@admin_bp.route("/categories/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/products", methods=["GET", "POST"])
@login_required
@admin_required
def products():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(status=True).all()]

    if form.validate_on_submit():
        image_url = ""
        if "image" in request.files:
            file = request.files["image"]
            if file.filename:
                saved = save_uploaded_image(file)
                if saved:
                    image_url = f"uploads/{saved}"

        product = Product(
            name=form.name.data,
            description=form.description.data or "",
            price=form.price.data,
            category_id=form.category_id.data,
            is_available=form.is_available.data,
            image_url=image_url,
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added", "success")
        return redirect(url_for("admin.products"))

    products = Product.query.all()
    return render_template("admin/products.html", products=products, form=form)


@admin_bp.route("/products/<int:id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_product(id):
    product = Product.query.get_or_404(id)
    product.is_available = not product.is_available
    db.session.commit()
    flash(f"Product {'enabled' if product.is_available else 'disabled'}", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/tables", methods=["GET", "POST"])
@login_required
@admin_required
def tables():
    form = TableForm()
    if form.validate_on_submit():
        table = create_table_with_qr(form.table_number.data)
        flash(f"Table {table.table_number} created with QR code", "success")
        return redirect(url_for("admin.tables"))

    tables = Table.query.order_by(Table.table_number).all()
    return render_template("admin/tables.html", tables=tables, form=form)


@admin_bp.route("/tables/<int:id>/qr")
@login_required
@admin_required
def table_qr(id):
    table = Table.query.get_or_404(id)
    qr_b64 = get_qr_image_base64(table.qr_token, request.host_url.rstrip("/"))
    return render_template("admin/qr_display.html", table=table, qr_b64=qr_b64)


@admin_bp.route("/tables/<int:id>/regenerate", methods=["POST"])
@login_required
@admin_required
def regenerate_table_qr(id):
    table = regenerate_qr_token(id)
    flash(f"QR code regenerated for Table {table.table_number}", "success")
    return redirect(url_for("admin.tables"))


@admin_bp.route("/tables/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_table(id):
    table = Table.query.get_or_404(id)
    db.session.delete(table)
    db.session.commit()
    flash("Table deleted", "success")
    return redirect(url_for("admin.tables"))


@admin_bp.route("/offers", methods=["GET", "POST"])
@login_required
@admin_required
def offers():
    form = OfferForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]

    if form.validate_on_submit():
        create_offer(
            product_id=form.product_id.data,
            offer_price=form.offer_price.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
        )
        flash("Special offer created", "success")
        return redirect(url_for("admin.offers"))

    offers = SpecialOffer.query.all()
    return render_template("admin/offers.html", offers=offers, form=form)


@admin_bp.route("/offers/<int:id>/deactivate", methods=["POST"])
@login_required
@admin_required
def deactivate(id):
    deactivate_offer(id)
    flash("Offer deactivated", "success")
    return redirect(url_for("admin.offers"))


@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    return render_template("admin/orders.html", orders=orders)


@admin_bp.route("/orders/<order_id>/cancel", methods=["POST"])
@login_required
@admin_required
def cancel_order(order_id):
    from app.services.order_service import update_order_status

    order = Order.query.get_or_404(order_id)
    if order.status in ["received", "preparing"]:
        update_order_status(order_id, "cancelled")
        flash(f"Order {order.id[:8]}... has been cancelled", "success")
    else:
        flash("Only active orders can be cancelled", "error")
    return redirect(url_for("admin.orders"))


@admin_bp.route("/notifications-mark-read", methods=["POST"])
@login_required
@admin_required
def mark_notifications_read():
    from flask import jsonify
    Order.query.update({})
    db.session.commit()
    return jsonify({"status": "success"})


@admin_bp.route("/notifications")
@login_required
@admin_required
def notifications():
    from flask import jsonify

    orders = Order.query.order_by(Order.created_at.desc()).limit(30).all()
    return jsonify([
        {
            "id": order.id,
            "table_number": order.table.table_number,
            "status": order.status,
            "total": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                }
                for item in order.items
            ],
        }
        for order in orders if not order.is_read
    ])


@admin_bp.route("/combos", methods=["GET", "POST"])
@login_required
@admin_required
def combos():
    form = ComboOfferForm()
    products = Product.query.filter_by(is_available=True).all()

    if request.method == "POST" and form.validate_on_submit():
        image_url = ""
        if "image" in request.files:
            file = request.files["image"]
            if file.filename:
                saved = save_uploaded_image(file)
                if saved:
                    image_url = f"uploads/{saved}"

        combo = ComboOffer(
            name=form.name.data,
            description=form.description.data or "",
            combo_price=form.combo_price.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            image_url=image_url,
        )
        db.session.add(combo)
        db.session.flush()

        product_ids = request.form.getlist("product_ids")
        quantities = request.form.getlist("quantities")
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                item = ComboItem(combo_id=combo.id, product_id=int(pid), quantity=int(qty))
                db.session.add(item)

        db.session.commit()
        flash("Combo offer created", "success")
        return redirect(url_for("admin.combos"))

    combos = ComboOffer.query.all()
    return render_template("admin/combos.html", combos=combos, form=form, products=products)


@admin_bp.route("/combos/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_combo(id):
    combo = ComboOffer.query.get_or_404(id)
    db.session.delete(combo)
    db.session.commit()
    flash("Combo deleted", "success")
    return redirect(url_for("admin.combos"))


@admin_bp.route("/combos/<int:id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_combo(id):
    combo = ComboOffer.query.get_or_404(id)
    combo.is_active = not combo.is_active
    db.session.commit()
    flash(f"Combo {'activated' if combo.is_active else 'deactivated'}", "success")
    return redirect(url_for("admin.combos"))

import os
from flask import Flask
from app.config import config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_cli_commands(app)

    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "warning"

    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from app.models import (
            Table,
            Category,
            Product,
            Order,
            OrderItem,
            SpecialOffer,
            StaffUser,
            Reservation,
        )


def register_blueprints(app):
    from app.blueprints.customer import customer_bp
    from app.blueprints.api import api_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.kitchen import kitchen_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(kitchen_bp)

    @app.route("/")
    def index():
        from flask import render_template
        from app.models.product import Product
        from app.services.offer_service import get_active_offers

        featured_products = Product.query.filter_by(is_available=True).limit(8).all()
        offers = get_active_offers()
        offer_map = {o.product_id: o for o in offers}

        return render_template(
            "home.html",
            featured_products=featured_products,
            offer_map=offer_map,
        )


def register_cli_commands(app):
    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Database tables created.")

    @app.cli.command("create-admin")
    def create_admin_command():
        from app.models.staff_user import StaffUser
        admin = StaffUser.query.filter_by(role="admin").first()
        if not admin:
            admin = StaffUser(name="Admin", email="admin@restaurant.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin@restaurant.com / admin123")
        else:
            print("Admin user already exists.")

    @app.cli.command("seed")
    def seed_command():
        from app.models.category import Category
        from app.models.product import Product
        from app.models.table import Table
        from app.models.staff_user import StaffUser
        from app.services.qr_service import create_table_with_qr

        if Category.query.first():
            print("Database already seeded.")
            return

        categories_data = [
            ("বিরিয়ানি ও পোলাও", 1),
            ("মাংস", 2),
            ("মাছ", 3),
            ("ভাত ও ডাল", 4),
            ("স্ন্যাকস", 5),
            ("ড্রিংকস", 6),
            ("মিষ্টি", 7),
        ]
        categories = {}
        for name, order in categories_data:
            c = Category(name=name, display_order=order)
            db.session.add(c)
            db.session.flush()
            categories[name] = c

        products_data = [
            ("বিরিয়ানি ও পোলাও", "কাচ্চি বিরিয়ানি", "খাসির মাংস ও সুগন্ধি চালের ঐতিহ্যবাহী কাচ্চি বিরিয়ানি", 320, "uploads/kacchi-biryani.jpg"),
            ("বিরিয়ানি ও পোলাও", "চিকেন বিরিয়ানি", "মুরগির মাংসের সুগন্ধি চিকেন বিরিয়ানি", 220, "uploads/chicken-biryani.jpg"),
            ("বিরিয়ানি ও পোলাও", "মোরগ পোলাও", "ঘি ও মসলায় রান্না করা ঐতিহ্যবাহী মোরগ পোলাও", 280, "uploads/morog-pulao.jpg"),
            ("বিরিয়ানি ও পোলাও", "ভুনা খিচুড়ি", "মরিচ ও মাংসের ঝোলসহ ঘন ভুনা খিচুড়ি", 180, "uploads/bhuna-khichuri.jpg"),
            ("বিরিয়ানি ও পোলাও", "তেহারি", "গরুর মাংসের ঝোলসহ সুগন্ধি তেহারি", 150, "uploads/tehari.jpg"),
            ("বিরিয়ানি ও পোলাও", "প্লেইন পোলাও", "সুগন্ধি চালের সাদা পোলাও", 120, "uploads/plain-pulao.jpg"),
            ("মাংস", "চিকেন কষা", "গাঢ় মশলাদার ঝোলের চিকেন কষা", 260, "uploads/chicken-korma.jpg"),
            ("মাংস", "গরুর মাংস ভুনা", "উপমহাদেশীয় মসলায় গরুর মাংস ভুনা", 340, "uploads/beef-bhuna.jpg"),
            ("মাংস", "চিকেন রোস্ট", "ঘি ও মসলায় রান্না করা চিকেন রোস্ট", 350, "uploads/chicken-roast.jpg"),
            ("মাংস", "বীফ রেজালা", "দুধ ও কেওড়া জল সহ বীফ রেজালা", 330, "uploads/beef-rezala.jpg"),
            ("মাংস", "চিকেন কারি", "সাদামাটা মশলাদার চিকেন কারি", 240, "uploads/chicken-curry.jpg"),
            ("মাছ", "চিংড়ি মালাইকারি", "নারকেল দুধে রান্না করা চিংড়ি মালাইকারি", 380, "uploads/chingri-malai.jpg"),
            ("মাছ", "ইলিশ ভাজা", "সরিষার তেলে ভাজা টাটকা ইলিশ", 450, "uploads/ilish-fish.jpg"),
            ("মাছ", "রুই মাছের ঝোল", "মরিচ ও হলুদে রুই মাছের পাতলা ঝোল", 180, "uploads/rohu-fish-curry.jpg"),
            ("ভাত ও ডাল", "সাদা ভাত", "সাদা সিদ্ধ চালের ভাত", 40, "uploads/steamed-rice.jpg"),
            ("ভাত ও ডাল", "মুসুর ডাল", "মসলা ফোড়ন দেওয়া মুসুর ডাল", 60, "uploads/lentil-dal.jpg"),
            ("ভাত ও ডাল", "আলু ভর্তা", "সরিষার তেল ও পেয়াজ দিয়ে আলু ভর্তা", 50, "uploads/aloo-bharta.jpg"),
            ("স্ন্যাকস", "চিকেন ফ্রাই", "ক্রিস্পি করে ভাজা চিকেন ফ্রাই", 220, "uploads/chicken-fry.jpg"),
            ("স্ন্যাকস", "বীফ টিক্কা", "কাঠিতে সেঁকা মশলাদার বীফ টিক্কা", 180, "uploads/beef-tikka.jpg"),
            ("স্ন্যাকস", "সমুচা", "আলু ও মাংসের পুর দেওয়া সমুচা", 40, "uploads/samosa.jpg"),
            ("স্ন্যাকস", "সিঙ্গারা", "খাস্তা ময়দার সিঙ্গারা", 30, "uploads/singara.jpg"),
            ("স্ন্যাকস", "ডিম ভুনা", "মশলার ঝোলসহ ডিম ভুনা", 80, "uploads/egg-curry.jpg"),
            ("ড্রিংকস", "বোরহানি", "টক-ঝাল মসলার ঐতিহ্যবাহী বোরহানি", 60, "uploads/borhani.jpg"),
            ("ড্রিংকস", "লাচ্ছি", "ঘন দইয়ের মিষ্টি লাচ্ছি", 120, "uploads/lassi.jpg"),
            ("ড্রিংকস", "কোল্ড কফি", "ঠান্ডা বরফসহ কোল্ড কফি", 150, "uploads/cold-coffee.jpg"),
            ("ড্রিংকস", "লেবু শরবত", "ঠান্ডা লেবু শরবত", 50, "uploads/lemonade.jpg"),
            ("ড্রিংকস", "মিনারেল ওয়াটার", "মিনারেল ওয়াটার (৫০০ মি.লি.)", 20, "uploads/water.jpg"),
            ("মিষ্টি", "মিষ্টি দই", "বগুড়ার ঐতিহ্যবাহী মিষ্টি দই", 90, "uploads/mishti-doi.jpg"),
            ("মিষ্টি", "রসমালাই", "দুধে ভেজানো নরম রসমালাই", 60, "uploads/roshmalai.jpg"),
            ("মিষ্টি", "ফিরনি", "চালের গুঁড়া ও দুধ দিয়ে তৈরি ফিরনি", 80, "uploads/firni.jpg"),
            ("মিষ্টি", "জিলাপি", "চিনির সিরায় ভেজানো জিলাপি", 50, "uploads/jalebi.jpg"),
        ]

        for cat_name, name, desc, price, image in products_data:
            p = Product(name=name, description=desc, price=price, category_id=categories[cat_name].id, image_url=image)
            db.session.add(p)

        for i in range(1, 9):
            create_table_with_qr(i)

        kitchen = StaffUser(name="Kitchen Staff", email="kitchen@restaurant.com", role="kitchen")
        kitchen.set_password("kitchen123")
        db.session.add(kitchen)

        db.session.commit()
        print("Database seeded with sample data.")
        print("Kitchen user: kitchen@restaurant.com / kitchen123")

    @app.cli.command("create-kitchen-user")
    def create_kitchen_user():
        from app.models.staff_user import StaffUser
        name = input("Name: ")
        email = input("Email: ")
        password = input("Password: ")
        user = StaffUser(name=name, email=email, role="kitchen")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Kitchen user created: {email}")

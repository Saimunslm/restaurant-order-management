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
        return "QR Restaurant Ordering System"


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
        from app.services.qr_service import create_table_with_qr

        if Category.query.first():
            print("Database already seeded.")
            return

        categories_data = [
            ("Starters", 1),
            ("Mains", 2),
            ("Drinks", 3),
            ("Desserts", 4),
        ]
        categories = {}
        for name, order in categories_data:
            c = Category(name=name, display_order=order)
            db.session.add(c)
            db.session.flush()
            categories[name] = c

        products_data = [
            ("Starters", "Spring Rolls", "Crispy vegetable spring rolls", 8.99),
            ("Starters", "Garlic Bread", "Toasted garlic bread with butter", 5.99),
            ("Starters", "Soup of the Day", "Chef's daily special soup", 6.99),
            ("Mains", "Grilled Chicken", "Herb-marinated grilled chicken breast", 18.99),
            ("Mains", "Beef Burger", "Angus beef burger with fries", 15.99),
            ("Mains", "Pasta Carbonara", "Classic Italian carbonara", 14.99),
            ("Mains", "Fish & Chips", "Beer-battered fish with chips", 16.99),
            ("Drinks", "Cola", "Refreshing cola drink", 2.99),
            ("Drinks", "Orange Juice", "Fresh squeezed orange juice", 3.99),
            ("Drinks", "Coffee", "Premium brewed coffee", 3.49),
            ("Drinks", "Water", "Still mineral water", 1.99),
            ("Desserts", "Chocolate Cake", "Rich chocolate fudge cake", 7.99),
            ("Desserts", "Ice Cream", "Vanilla ice cream scoop", 4.99),
            ("Desserts", "Cheesecake", "New York style cheesecake", 8.99),
        ]

        for cat_name, name, desc, price in products_data:
            p = Product(name=name, description=desc, price=price, category_id=categories[cat_name].id)
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

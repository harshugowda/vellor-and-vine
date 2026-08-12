from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from datetime import datetime

# -----------------------------
# Product Model
# -----------------------------
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200), default="default.jpg")
    stock = db.Column(db.Integer, default=0)
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    description = db.Column(db.Text)

   


# -----------------------------
# User Model
# -----------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
# -----------------------------
# Order Model
# -----------------------------
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    total = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending Confirmation"
    )

    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )
# -----------------------------
# Notification Model
# -----------------------------

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    message = db.Column(
        db.String(255),
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="notifications"
    )

    order = db.relationship(
        "Order",
        backref="notifications"
    )
# -----------------------------
# Order Items
# -----------------------------
class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)

    price = db.Column(db.Float, nullable=False)

    order = db.relationship("Order", backref="items")

    product = db.relationship("Product")
# -----------------------------
# Wishlist Model
# -----------------------------

class Wishlist(db.Model):

    __tablename__ = "wishlist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="wishlist_items"
    )

    product = db.relationship(
        "Product",
        backref="wishlist_items"
    )
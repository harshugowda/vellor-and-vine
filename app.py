from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from flask import send_file
import os
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session,flash
from datetime import datetime
from models import Product, db, User, Order, Category, OrderItem, Notification, Wishlist
app = Flask(__name__)
app.config.from_object("config.Config")


db.init_app(app)


# -----------------------------
# Product Model
# -----------------------------
#class Product(db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    #name = db.Column(db.String(100), nullable=False)
   # category = db.Column(db.String(50), nullable=False)
    #price = db.Column(db.Float, nullable=False)
    #description = db.Column(db.Text)
    #image = db.Column(db.String(200), default="default.jpg")

# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():

    products = Product.query.limit(4).all()

    return render_template(
        "index.html",
        products=products
    )

# -----------------------------
# Shop Page
# -----------------------------
from sqlalchemy import asc, desc

@app.route("/shop")
def shop():

    sort = request.args.get("sort")

    if sort == "price_low":
        products = Product.query.order_by(Product.price.asc()).all()

    elif sort == "price_high":
        products = Product.query.order_by(Product.price.desc()).all()

    elif sort == "name":
        products = Product.query.order_by(Product.name.asc()).all()

    else:
        products = Product.query.all()

    return render_template(
        "shop.html",
        products=products
    )

# -----------------------------
# Admin Page
# -----------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    
    if not session.get("is_admin"):
        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        description = request.form["description"]

        image = request.files["image"]

        filename = "default.jpg"

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        product = Product(
         name=name,
         category=category,
         price=price,
         stock=stock,
         description=description,
         image=filename
)

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("admin"))

    products = Product.query.all()

    return render_template("admin.html", products=products)


# 👇 PASTE THE NEW CODE HERE

@app.route("/delete/<int:id>")
def delete_product(id):

    product = Product.query.get_or_404(id)

    db.session.delete(product)

    db.session.commit()

    return redirect(url_for("admin"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        product.name = request.form["name"]
        product.category = request.form["category"]
        product.price = float(request.form["price"])
        product.description = request.form["description"]

        db.session.commit()

        return redirect(url_for("admin"))

    return render_template("edit.html", product=product)
@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):

    product = Product.query.get_or_404(id)

    if product.stock <= 0:
        return "This product is currently out of stock."

    cart = session.get("cart", {})

    # Convert old list cart to dictionary
    if isinstance(cart, list):

        new_cart = {}

        for pid in cart:

            pid = str(pid)

            new_cart[pid] = new_cart.get(pid, 0) + 1

        cart = new_cart

    product_id = str(id)

    # Get requested quantity
    try:
        quantity = int(request.args.get("quantity", 1))
    except ValueError:
        quantity = 1

    # Make sure quantity is valid
    if quantity < 1:
        quantity = 1

    # Check stock
    if quantity > product.stock:
        quantity = product.stock

    # Add quantity to existing cart quantity
    current_quantity = cart.get(product_id, 0)

    new_quantity = current_quantity + quantity

    # Never exceed available stock
    if new_quantity > product.stock:
        new_quantity = product.stock

    cart[product_id] = new_quantity

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))

@app.route("/update-cart/<int:id>", methods=["POST"])
def update_cart(id):

    product = Product.query.get_or_404(id)

    cart = session.get("cart", {})

    product_id = str(id)

    if product_id not in cart:
        return redirect(url_for("cart"))

    try:
        quantity = int(request.form["quantity"])
    except (ValueError, TypeError):
        quantity = 1

    # Minimum quantity
    if quantity < 1:
        quantity = 1

    # Don't allow more than available stock
    if quantity > product.stock:
        quantity = product.stock

    cart[product_id] = quantity

    session["cart"] = cart
    session.modified = True

    return redirect(url_for("cart"))

@app.route("/increase/<int:id>")
def increase_quantity(id):

    cart = session.get("cart", {})

    product = Product.query.get_or_404(id)

    product_id = str(id)

    if product_id in cart:
        if cart[product_id] < product.stock:
            cart[product_id] += 1

    session["cart"] = cart

    return redirect(url_for("cart"))

@app.route("/decrease/<int:id>")
def decrease_quantity(id):

    cart = session.get("cart", {})

    product_id = str(id)

    if product_id in cart:

        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))

@app.route("/remove-from-cart/<int:id>")
def remove_from_cart(id):

    cart = session.get("cart", {})

    product_id = str(id)

    if product_id in cart:
        del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))
@app.route("/cart")
def cart():

    cart = session.get("cart", {})

    products = []

    total = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:

            subtotal = product.price * quantity

            total += subtotal

            products.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

    return render_template(
        "cart.html",
        products=products,
        total=total
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists!"

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin

            return redirect(url_for("home"))

        return "Invalid Email or Password"

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route("/product/<int:id>")
def product(id):

    product = Product.query.get_or_404(id)

    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()

    return render_template(
        "product.html",
        product=product,
        related_products=related_products
    )
# -----------------------------
# Wishlist
# -----------------------------

@app.route("/wishlist/<int:product_id>")
def add_to_wishlist(product_id):

    # User must be logged in
    if not session.get("user_id"):
        return redirect(url_for("login"))

    product = Product.query.get_or_404(product_id)

    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=session["user_id"],
        product_id=product.id
    ).first()

    if not existing:
        wishlist = Wishlist(
            user_id=session["user_id"],
            product_id=product.id
        )

        db.session.add(wishlist)
        db.session.commit()

    return redirect(request.referrer or url_for("shop"))
@app.route("/my-wishlist")
def my_wishlist():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    wishlist_items = Wishlist.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )

@app.route("/remove-wishlist/<int:wishlist_id>")
def remove_wishlist(wishlist_id):

    if not session.get("user_id"):
        return redirect(url_for("login"))

    item = Wishlist.query.filter_by(
        id=wishlist_id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("my_wishlist"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", {})

    products = []
    total = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:

            subtotal = product.price * quantity

            total += subtotal

            products.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

    if request.method == "POST":

        order = Order(
            customer_name=request.form["fullname"],
            email=request.form["email"],
            phone=request.form["phone"],
            address=request.form["address"],
            total=total,
            user_id=session.get("user_id")
        )

        db.session.add(order)
        db.session.flush()

        # Save purchased products
        for item in products:

            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product"].id,
                quantity=item["quantity"],
                price=item["product"].price
            )

            db.session.add(order_item)


        # Reduce stock
        for item in products:
            item["product"].stock -= item["quantity"]

        db.session.commit()

        # Empty cart
        session["cart"] = {}

        return redirect(
            url_for("order_success", order_id=order.id)
        )

    return render_template(
        "checkout.html",
        total=total,
        products=products
    )





class ChatMessage(db.Model):

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
        db.Text,
        nullable=False
    )

    sender = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="chat_messages"
    )

    order = db.relationship(
        "Order",
        backref="chat_messages"
    )
@app.route("/chat/<int:order_id>")
def order_chat(order_id):

    if not session.get("user_id"):
        return redirect(url_for("login"))

    order = Order.query.get_or_404(order_id)

    if order.user_id != session["user_id"]:
        return redirect(url_for("my_orders"))

    messages = ChatMessage.query.filter_by(
        order_id=order.id
    ).order_by(
        ChatMessage.created_at.asc()
    ).all()

    return render_template(
        "chat.html",
        order=order,
        messages=messages
    )
@app.route("/chat/<int:order_id>/paid", methods=["POST"])

def mark_payment_claimed(order_id):

    if not session.get("user_id"):
        return redirect(url_for("login"))

    order = Order.query.get_or_404(order_id)

    if order.user_id != session["user_id"]:
        return redirect(url_for("my_orders"))

    order.payment_status = "Payment Claimed"

    db.session.commit()

    return redirect(
        url_for(
            "order_chat",
            order_id=order.id
        )
    )
@app.route("/admin/chat/<int:order_id>/confirm-payment", methods=["POST"])
def confirm_payment(order_id):

    if not session.get("is_admin"):
        return redirect(url_for("login"))

    order = Order.query.get_or_404(order_id)

    order.payment_status = "Paid"

    db.session.commit()

    return redirect(
        url_for(
            "admin_chat",
            order_id=order.id
        )
    )
@app.route("/admin/chat/<int:order_id>")
def admin_chat(order_id):

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    order = Order.query.get_or_404(order_id)

    messages = ChatMessage.query.filter_by(
        order_id=order.id
    ).order_by(
        ChatMessage.created_at.asc()
    ).all()

    return render_template(
        "admin_chat.html",
        order=order,
        messages=messages
    )
@app.route("/admin/chat/<int:order_id>/send-qr")
def admin_send_qr(order_id):

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    order = Order.query.get_or_404(order_id)

    admin_id = session.get("user_id")

    if not admin_id:
        return redirect(url_for("login"))

    message = ChatMessage(
        user_id=admin_id,
        order_id=order.id,
        message="[PAYMENT_QR]",
        sender="admin"
    )

    db.session.add(message)
    db.session.commit()

    return redirect(
        url_for(
            "admin_chat",
            order_id=order.id
        )
    )


@app.route("/admin/chat/<int:order_id>/send", methods=["POST"])
def admin_send_chat(order_id):

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    order = Order.query.get_or_404(order_id)

    message_text = request.form.get(
        "message",
        ""
    ).strip()

    if message_text:

        message = ChatMessage(
            user_id=session.get("user_id"),
            order_id=order.id,
            message=message_text,
            sender="admin"
        )

        db.session.add(message)
        db.session.commit()

    return redirect(
        url_for(
            "admin_chat",
            order_id=order.id
        )
    )


@app.route("/chat/<int:order_id>/send", methods=["POST"])
def send_order_chat_message(order_id):

    if not session.get("user_id"):
        return redirect(url_for("login"))

    order = Order.query.get_or_404(order_id)

    if order.user_id != session["user_id"]:
        return redirect(url_for("my_orders"))

    message_text = request.form.get(
        "message",
        ""
    ).strip()

    if message_text:

        message = ChatMessage(
            user_id=session["user_id"],
            order_id=order.id,
            message=message_text,
            sender="customer"
        )

        db.session.add(message)
        db.session.commit()

    return redirect(
        url_for(
            "order_chat",
            order_id=order.id
        )
    )

@app.route("/invoice/<int:order_id>")
def invoice(order_id):

    order = Order.query.get_or_404(order_id)

    order_items = OrderItem.query.filter_by(
        order_id=order.id
    ).all()

    invoice_folder = os.path.join("static", "invoices")

    os.makedirs(invoice_folder, exist_ok=True)

    file_path = os.path.join(
        invoice_folder,
        f"invoice_{order.id}.pdf"
    )

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "VELLOR &amp; VINE",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            "Luxury Handmade Crochet",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Invoice No: #{order.id}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Customer: {order.customer_name}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Email: {order.email}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Phone: {order.phone}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Address: {order.address}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>Order Items</b>",
            styles["Heading2"]
        )
    )

    for item in order_items:

        subtotal = item.quantity * item.price

        story.append(
            Paragraph(
                f"{item.product.name} | "
                f"Qty: {item.quantity} | "
                f"Price: ₹{item.price:.2f} | "
                f"Subtotal: ₹{subtotal:.2f}",
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Total: ₹{order.total:.2f}</b>",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "Thank you for shopping with Vellor &amp; Vine!",
            styles["Normal"]
        )
    )

    doc.build(story)

    return send_file(
        file_path,
        as_attachment=True
    )

@app.route("/payment")
def payment():

    return "<h1>💳 Razorpay Payment Coming Soon...</h1>"

@app.route("/order-success/<int:order_id>")
def order_success(order_id):

    order = Order.query.get_or_404(order_id)

    return render_template(
        "order_success.html",
        order=order
    )

@app.route("/orders")
def orders():
    if not session.get("is_admin"):
       return redirect(url_for("home"))

    all_orders = Order.query.all()

    return render_template(
        "orders.html",
        orders=all_orders
    )
@app.route("/update-order/<int:id>", methods=["POST"])
def update_order(id):

    order = Order.query.get_or_404(id)

    new_status = request.form["status"]

    # Update order status
    order.status = new_status

    # Create customer notification
    if order.user_id:

        notification = Notification(
            user_id=order.user_id,
            order_id=order.id,
            message=f"Your Order #{order.id} is now {new_status}."
        )

        db.session.add(notification)

    db.session.commit()

    flash(
        f"Order #{order.id} status updated to {new_status}.",
        "success"
    )

    return redirect(url_for("orders"))

# -----------------------------@app.route("/profile")
@app.route("/categories", methods=["GET", "POST"])
def categories():
    if not session.get("is_admin"):
        return redirect(url_for("home"))

    if request.method == "POST":

        category = Category(
            name=request.form["name"],
            description=request.form["description"]
        )

        db.session.add(category)
        db.session.commit()

        return redirect(url_for("categories"))

    categories = Category.query.all()

    return render_template(
        "categories.html",
        categories=categories
    )
@app.route("/search")
def search():

    query = request.args.get("q", "")

    products = Product.query.filter(
        Product.name.ilike(f"%{query}%")
    ).all()

    return render_template(
        "shop.html",
        products=products
    )
@app.route("/dashboard")
def dashboard():

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    # -----------------------------
    # Basic Statistics
    # -----------------------------

    total_products = Product.query.count()

    total_users = User.query.count()

    total_orders = Order.query.count()


    # -----------------------------
    # Revenue
    # -----------------------------

    orders = Order.query.all()

    revenue = sum(
        order.total for order in orders
    )


    # -----------------------------
    # Order Status Statistics
    # -----------------------------

    pending_orders = Order.query.filter(
        Order.status == "Pending"
    ).count()

    confirmed_orders = Order.query.filter(
        Order.status == "Confirmed"
    ).count()

    processing_orders = Order.query.filter(
        Order.status == "Processing"
    ).count()

    shipped_orders = Order.query.filter(
        Order.status == "Shipped"
    ).count()

    delivered_orders = Order.query.filter(
        Order.status == "Delivered"
    ).count()

    cancelled_orders = Order.query.filter(
        Order.status == "Cancelled"
    ).count()


    # -----------------------------
    # Recent Orders
    # -----------------------------

    recent_orders = Order.query.order_by(
        Order.id.desc()
    ).limit(5).all()


    # -----------------------------
    # Low Stock
    # -----------------------------

    low_stock = Product.query.filter(
        Product.stock <= 5
    ).all()


    # -----------------------------
    # Dashboard
    # -----------------------------

    return render_template(
        "dashboard.html",

        total_products=total_products,

        total_users=total_users,

        total_orders=total_orders,

        revenue=revenue,

        pending_orders=pending_orders,

        confirmed_orders=confirmed_orders,

        processing_orders=processing_orders,

        shipped_orders=shipped_orders,

        delivered_orders=delivered_orders,

        cancelled_orders=cancelled_orders,

        recent_orders=recent_orders,

        low_stock=low_stock
    )
@app.route("/make-admin")
def make_admin():

    user = User.query.filter_by(email="hharshitha2001@gmail.com").first()

    if not user:
        return "User not found."

    #before = user.is_admin

    user.is_admin = True

    db.session.commit()

    #db.session.refresh(user)

    #return f"Before: {before} | After: {user.is_admin}"
    return "you are now an admin!"

@app.route("/users")
def users():

    users = User.query.all()

    output = ""

    for user in users:
        output += (
            f"ID: {user.id} | "
            f"Name: {user.name} | "
            f"Email: {user.email} | "
            f"Admin: {user.is_admin}<br>"
        )

    return output
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    return render_template("profile.html", user=user)

@app.route("/my-orders")
def my_orders():

    if "user_id" not in session:
        return redirect(url_for("login"))

    orders = Order.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Order.id.desc()).all()

    return render_template(
        "my_orders.html",
        orders=orders
    )
@app.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    notifications = Notification.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Notification.created_at.desc()
    ).all()

    # Mark all notifications as read
    for notification in notifications:
        notification.is_read = True

    db.session.commit()

    return render_template(
        "notifications.html",
        notifications=notifications
    )
@app.route("/notifications/read/<int:notification_id>")
def mark_notification_read(notification_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=session["user_id"]
    ).first_or_404()

    notification.is_read = True

    db.session.commit()

    return redirect(url_for("notifications"))

@app.context_processor
def notification_count():

    if "user_id" in session:

        unread_count = Notification.query.filter_by(
            user_id=session["user_id"],
            is_read=False
        ).count()

    else:

        unread_count = 0

    return {
        "unread_notifications": unread_count
    }
# -----------------------------
# Wishlist Model
# -----------------------------


# Run App
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
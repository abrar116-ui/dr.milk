from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem
from extensions import db
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

from flask import current_app
# --- Admin Routes ---

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='admin').first()
        if user and user.check_password(password):
            login_user(user)
            # Track Login
            activity = LoginActivity(user_id=user.id, activity_type='login')
            db.session.add(activity)
            db.session.commit()
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return render_template('admin/login.html', error='Invalid admin credentials')
    
    return render_template('admin/login.html')

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    from sqlalchemy import func
    from models import ist_now
    today_dt = ist_now()
    today = today_dt.date()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    # Analytics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Login stats
    logins_today = LoginActivity.query.filter(
        func.date(LoginActivity.timestamp) == today_str,
        LoginActivity.activity_type == 'login'
    ).count()
    
    logouts_today = LoginActivity.query.filter(
        func.date(LoginActivity.timestamp) == today_str,
        LoginActivity.activity_type == 'logout'
    ).count()
    
    # Order stats
    orders_today = Order.query.filter(func.date(Order.created_at) == today_str).count()
    orders_yesterday = Order.query.filter(func.date(Order.created_at) == yesterday_str).count()
    
    # Milk stats (liters)
    milk_today = db.session.query(func.sum(Order.total_liters)).filter(
        func.date(Order.created_at) == today_str
    ).scalar() or 0
    
    today_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today_str
    ).scalar() or 0
        
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'logins_today': logins_today,
        'logouts_today': logouts_today,
        'orders_today': orders_today,
        'orders_yesterday': orders_yesterday,
        'milk_today': round(milk_today, 2),
        'today_revenue': round(today_revenue, 2),
        'total_revenue': round(total_revenue, 2),
        'now_text': today_dt.strftime('%B %d, %Y')
    }
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Charts Data - Real Time from DB
    labels = []
    datasets = defaultdict(list)
    product_names = [p.name for p in Product.query.filter_by(category='Milk').all()]
    if not product_names:
        product_names = ['A2 Cow Milk', 'Buffalo Milk']
        
    for i in range(6, -1, -1):
        target_date = today_dt - timedelta(days=i)
        target_str = target_date.strftime('%Y-%m-%d')
        labels.append(target_date.strftime('%a')) # Mon, Tue
        
        items_today = db.session.query(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).join(Order, OrderItem.order_id == Order.id).filter(
            func.date(Order.created_at) == target_str,
            Product.category == 'Milk'
        ).all()
        
        day_liters = {name: 0.0 for name in product_names}
        for item, product in items_today:
            if product.name in day_liters:
                day_liters[product.name] += (item.liter_total or 0.0)
                
        for name in product_names:
            datasets[name].append(day_liters[name])

    chart_datasets = []
    colors = ['rgba(212, 175, 55, 0.8)', 'rgba(46, 204, 113, 0.8)', 'rgba(52, 152, 219, 0.8)', 'rgba(231, 76, 60, 0.8)']
    for i, (name, data) in enumerate(datasets.items()):
        color = colors[i % len(colors)]
        chart_datasets.append({
            'label': name + ' (Liters)',
            'data': data,
            'backgroundColor': color,
            'borderColor': color.replace('0.8', '1'),
            'borderWidth': 1
        })
        
    chart_data = {
        'labels': labels,
        'datasets': chart_datasets
    }

    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, chart_data=chart_data)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    delta = datetime.now() - user.created_at
    months = delta.days // 30
    
    # Calculate Monthly Subscription Stats & History (Similar to user profile)
    from models import ist_now
    now = ist_now()
    month_name = now.strftime('%B')
    year = now.year
    month = now.month
    
    active_orders = Order.query.filter(
        Order.user_id == user.id,
        Order.status != 'Cancelled'
    ).all()
    
    import calendar
    num_days = calendar.monthrange(year, month)[1]
    
    month_sheet = []
    delivery_days_count = 0
    total_month_spent = 0.0
    
    for day_num in range(1, num_days + 1):
        date_obj = datetime(year, month, day_num)
        day_name = date_obj.strftime('%a')
        
        day_deliveries = []
        for order in active_orders:
            if order.delivery_days and day_name in order.delivery_days:
                for item in order.items:
                    day_deliveries.append({
                        'product': item.product.name if item.product else "Unknown",
                        'size': item.size,
                        'quantity': item.quantity,
                        'amount': item.price * item.quantity
                    })
                    total_month_spent += (item.price * item.quantity)
        
        if day_deliveries:
            delivery_days_count += 1
            month_sheet.append({
                'date': date_obj.strftime('%d %b'),
                'day': date_obj.strftime('%A'),
                'is_past': date_obj.date() < now.date(),
                'is_today': date_obj.date() == now.date(),
                'deliveries': day_deliveries
            })

    stats = {
        'month_name': month_name,
        'total_delivery_days': delivery_days_count,
        'total_spent': total_month_spent,
        'month_sheet': month_sheet,
        'active_subscriptions': active_orders
    }
    
    return render_template('admin/user_profile.html', user=user, sub_months=months, stats=stats)

@admin_bp.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/admin/products/add', methods=['POST'])
@login_required
@admin_required
def admin_add_product():
    name = request.form.get('name')
    category = request.form.get('category')
    description = request.form.get('description')
    
    # Handle Image Upload or URL
    image = request.form.get('image')
    image_file = request.files.get('image_file')
    
    if image_file and getattr(image_file, 'filename', ''):
        import werkzeug.utils
        filename = werkzeug.utils.secure_filename(getattr(image_file, 'filename'))
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image = filename

    # Create product
    new_product = Product(
        name=name,
        category=category,
        description=description,
        image=image,
        benefits=[]
    )
    db.session.add(new_product)
    db.session.flush()

    # Add pricing variants
    size1 = request.form.get('size1')
    price1 = request.form.get('price1')
    if size1 and price1:
        v1 = ProductVariant(product_id=new_product.id, size=size1, price=float(price1))
        db.session.add(v1)
        
    size2 = request.form.get('size2')
    price2 = request.form.get('price2')
    if size2 and price2:
        v2 = ProductVariant(product_id=new_product.id, size=size2, price=float(price2))
        db.session.add(v2)

    db.session.commit()
    flash('Product added successfully', 'success')
    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/admin/products/delete/<int:id>')
@login_required
@admin_required
def admin_delete_product(id):
    product = Product.query.get_or_404(id)
    # Delete variants first to maintain relational integrity
    ProductVariant.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    # Group orders by date
    grouped = defaultdict(list)
    for order in orders:
        date_key = order.created_at.strftime('%Y-%m-%d')
        grouped[date_key].append(order)
    
    # Create a sorted list of (formatted_date, orders)
    sorted_date_keys = sorted(grouped.keys(), reverse=True)
    display_orders = []
    
    for d_key in sorted_date_keys:
        # Create a datetime object to format it nicely
        dt = datetime.strptime(d_key, '%Y-%m-%d')
        formatted_date = dt.strftime('%A, %d %B %Y')
        display_orders.append({
            'date': formatted_date,
            'orders': grouped[d_key]
        })
    
    return render_template('admin/orders.html', display_orders=display_orders)

@admin_bp.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    db.session.commit()
    return redirect(url_for('admin.admin_orders'))

@admin_bp.route('/admin/orders/delete/<int:id>')
@login_required
@admin_required
def admin_delete_order(id):
    order = Order.query.get_or_404(id)
    # Also delete associated items
    OrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully', 'success')
    return redirect(url_for('admin.admin_orders'))

@admin_bp.route('/admin/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    import csv
    from io import StringIO
    from flask import make_response

    si = StringIO()
    cw = csv.writer(si)
    
    if report_type == 'users':
        cw.writerow(['ID', 'Username', 'Email', 'Phone', 'Address', 'Status', 'Registered At'])
        users = User.query.all()
        for u in users:
            cw.writerow([u.id, u.username, u.email, u.phone, u.address, u.is_active, u.created_at])
    elif report_type == 'orders':
        cw.writerow(['Order ID', 'User', 'Amount', 'Liters', 'Status', 'Date'])
        orders = Order.query.all()
        for o in orders:
            cw.writerow([o.order_id, o.user.username, o.total_amount, o.total_liters, o.status, o.created_at])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={report_type}_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@admin_bp.route('/admin/quick_delivery', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_quick_delivery():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        product_id = request.form.get('product_id')
        size = request.form.get('size')
        quantity = int(request.form.get('quantity', 1))

        if not user_id or not product_id or not size:
            flash('Please select all required fields', 'danger')
            return redirect(url_for('admin.admin_quick_delivery'))

        user = User.query.get(user_id)
        product = Product.query.get(product_id)
        variant = ProductVariant.query.filter_by(product_id=product_id, size=size).first()

        if not user or not product or not variant:
            flash('Invalid selection', 'danger')
            return redirect(url_for('admin.admin_quick_delivery'))
            
        import uuid
        order_id = str(uuid.uuid4())[:8].upper()

        # Create Order
        new_order = Order(
            user_id=user.id,
            total_amount=variant.price * quantity,
            total_liters=(variant.liter_value or 0) * quantity,
            status='Delivered', # Instant delivery logging
            delivery_time='Morning',
            delivery_days=[],
            order_id=order_id
        )
        
        db.session.add(new_order)
        db.session.flush()

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            size=size,
            quantity=quantity,
            price=variant.price,
            liter_total=(variant.liter_value or 0) * quantity
        )
        db.session.add(order_item)
        db.session.commit()

        flash(f'Delivery logged successfully for {user.username}', 'success')
        return redirect(url_for('admin.admin_quick_delivery'))

    # GET Request
    users = User.query.filter_by(role='customer', is_active=True).all()
    # Serialize user data for frontend JS
    users_data = {}
    for u in users:
        users_data[u.id] = {
            'username': u.username,
            'name': u.username,
            'address': u.address or '-',
            'society': u.society or '-',
            'block': u.block or '-',
            'flat_number': u.flat_number or '-',
            'phone': u.phone or '-'
        }
        
    products = Product.query.all()
    products_data = {}
    for p in products:
        variants = []
        for v in p.variants:
            variants.append({'size': v.size, 'price': v.price})
        products_data[p.id] = {
            'name': p.name,
            'category': p.category,
            'variants': variants
        }

    return render_template('admin/quick_delivery.html', users=users, users_data=json.dumps(users_data), products=products, products_data=json.dumps(products_data))



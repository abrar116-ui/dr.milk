from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import User, LoginActivity, Product, ProductVariant, Order, OrderItem
from extensions import db, login_manager
from datetime import datetime, timedelta
from collections import defaultdict
import json

user_bp = Blueprint('user', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@user_bp.route('/')
def home():
    category = request.args.get('category')
    if category:
        products_query = Product.query.filter_by(category=category).all()
    else:
        products_query = Product.query.all()
    
    # Format products for template to match previous structure
    formatted_products = []
    for p in products_query:
        prices = {v.size: v.price for v in p.variants}
        formatted_products.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'benefits': p.benefits,
            'image': p.image,
            'prices': prices
        })

    # Personal Greeting Logic
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    features = [
        {'title': '100% Pure & Natural', 'description': 'No additives, preservatives, or chemicals', 'icon': '✓'},
        {'title': 'Own Farm Production', 'description': 'Complete control over quality from farm to home', 'icon': '🌾'},
        {'title': 'Glass Bottle Packaging', 'description': 'Eco-friendly and maintains milk freshness', 'icon': '🔷'},
        {'title': 'Daily Fresh Delivery', 'description': 'Delivered fresh to your doorstep every morning', 'icon': '🚚'},
        {'title': 'Certified & Tested', 'description': 'Food safety certified with rigorous quality testing', 'icon': '✅'},
        {'title': 'Pasteurization', 'description': 'Heat-treated for safety while maintaining nutritional value', 'icon': '🔥'},
        {'title': 'Sustainable & Eco Friendly', 'description': 'Environment-conscious farming and packaging', 'icon': '🌱'}
    ]

    return render_template('index.html', 
                         products=formatted_products, 
                         features=features, 
                         greeting=greeting)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Track Login
            activity = LoginActivity(user_id=user.id, activity_type='login')
            db.session.add(activity)
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('user.home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        if not email: email = None
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')

        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='Username already exists')

        new_user = User(
            username=username, 
            email=email,
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            society=request.form.get('society'),
            block=request.form.get('block'),
            flat_number=request.form.get('flat_number')
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('user.home'))

    return render_template('signup.html')

@user_bp.route('/logout')
@login_required
def logout():
    activity = LoginActivity(user_id=current_user.id, activity_type='logout')
    db.session.add(activity)
    db.session.commit()
    logout_user()
    return redirect(url_for('user.login'))

@user_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    product_id = int(data.get('product_id'))
    size = data.get('size')
    quantity = int(data.get('quantity', 1))
    
    meta = data.get('meta')
    
    if 'cart' not in session:
        session['cart'] = []
    
    # If it's a subscription (has meta), always add as a new item to keep preferences separate
    # Otherwise, merge identical items
    if meta:
        session['cart'].append({'product_id': product_id, 'size': size, 'quantity': quantity, 'meta': meta})
    else:
        cart_item = next((item for item in session['cart'] if item['product_id'] == product_id and item['size'] == size and 'meta' not in item), None)
        if cart_item:
            cart_item['quantity'] += quantity
        else:
            session['cart'].append({'product_id': product_id, 'size': size, 'quantity': quantity})
    
    session.modified = True
    return jsonify({'success': True, 'message': 'Added to cart'})

@user_bp.route('/remove_from_cart/<int:product_id>/<size>', methods=['POST'])
@login_required
def remove_from_cart(product_id, size):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if not (item['product_id'] == product_id and item['size'] == size)]
        session.modified = True
    return jsonify({'success': True, 'message': 'Item removed'})

@user_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if not session.get('cart'):
        flash('Your cart is empty', 'warning')
        return redirect(url_for('user.home'))
        
    cart_items = session.get('cart', [])
    total_amount = 0.0
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                total_amount += variant.price * item['quantity']

    if request.method == 'POST':
        # Update User Data PREVIEW / Checkout fields (Point 7)
        phone = request.form.get('phone')
        address = request.form.get('address')
        if phone: current_user.phone = phone
        if address: current_user.address = address
        society = request.form.get('society')
        if society: current_user.society = society
        block = request.form.get('block')
        if block: current_user.block = block
        flat_number = request.form.get('flat_number')
        if flat_number: current_user.flat_number = flat_number
        db.session.commit()

        total_amount = 0.0
        total_liters = 0.0
        
        from models import ist_now
        # In a real app, generate a unique order_id
        import uuid
        order_id = str(uuid.uuid4())[:8].upper()
        
        # Get delivery days from form
        days_json = request.form.get('delivery_days', '[]')
        try:
            days = json.loads(days_json)
        except:
            days = []
            
        # Create Subscription Order (1 Month)
        new_order = Order(
            user_id=current_user.id,
            total_amount=0, # temp
            total_liters=0, # temp
            status='Active',
            delivery_time=request.form.get('delivery_time', 'Morning'),
            delivery_days=days,
            is_subscription=True,
            subscription_end=ist_now() + timedelta(days=30),
            order_id=order_id
        )
        
        db.session.add(new_order)
        db.session.flush()
        
        for item in cart_items:
            product = Product.query.get(item['product_id'])
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                item_total = variant.price * item['quantity']
                total_amount += item_total
                
                # Liters tracking
                liters = (variant.liter_value or 0) * item['quantity']
                total_liters += liters
                
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    size=item['size'],
                    quantity=item['quantity'],
                    price=variant.price,
                    liter_total=liters
                )
                db.session.add(order_item)
                
        new_order.total_amount = total_amount
        new_order.total_liters = total_liters
        
        db.session.commit()
        session.pop('cart', None)
        flash('Order placed successfully!', 'success')
        return redirect(url_for('user.user_orders'))
        
    return render_template('checkout.html', total_amount=total_amount)

@user_bp.route('/cart')
@login_required
def view_cart():
    cart_items = session.get('cart', [])
    cart_details = []
    total_amount = 0.0
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            variant = ProductVariant.query.filter_by(product_id=product.id, size=item['size']).first()
            if variant:
                item_total = variant.price * item['quantity']
                total_amount += item_total
                cart_details.append({
                    'product': product,
                    'size': item['size'],
                    'quantity': item['quantity'],
                    'price': variant.price,
                    'item_total': item_total
                })
    return render_template('cart.html', cart_details=cart_details, total_amount=total_amount)

@user_bp.route('/orders')
@login_required
def user_orders():
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Calculate today and tomorrow days (e.g., 'Mon', 'Tue')
    today_day = datetime.now().strftime('%a')
    tomorrow_day = (datetime.now() + timedelta(days=1)).strftime('%a')
    
    today_orders = [o for o in all_orders if today_day in (o.delivery_days or [])]
    tomorrow_orders = [o for o in all_orders if tomorrow_day in (o.delivery_days or [])]
    
    # Filter all_orders to not include today/tomorrow deliveries (pure history)
    history_orders = [o for o in all_orders if o not in today_orders and o not in tomorrow_orders]
    
    # Group history orders by date
    grouped_history = defaultdict(list)
    for order in history_orders:
        date_key = order.created_at.strftime('%Y-%m-%d')
        grouped_history[date_key].append(order)
    
    # Create sorted list of (formatted_date, orders)
    sorted_history_keys = sorted(grouped_history.keys(), reverse=True)
    display_history = []
    for d_key in sorted_history_keys:
        dt = datetime.strptime(d_key, '%Y-%m-%d')
        display_history.append({
            'date': dt.strftime('%A, %d %B %Y'),
            'orders': grouped_history[d_key]
        })
    
    return render_template('orders.html', 
                         today_orders=today_orders, 
                         tomorrow_orders=tomorrow_orders, 
                         display_history=display_history)

@user_bp.route('/cancel_subscription/<int:order_id>', methods=['POST'])
@login_required
def cancel_subscription(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('user.profile'))
    order.status = 'Cancelled'
    db.session.commit()
    flash('Subscription cancelled successfully.', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        current_user.society = request.form.get('society')
        current_user.block = request.form.get('block')
        current_user.flat_number = request.form.get('flat_number')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    # Calculate Monthly Subscription Stats
    from models import ist_now
    now = ist_now()
    month_name = now.strftime('%B')
    year = now.year
    month = now.month
    
    # Get all active subscriptions/orders for this user
    active_orders = Order.query.filter(
        Order.user_id == current_user.id,
        Order.status != 'Cancelled'
    ).all()
    
    import calendar
    num_days = calendar.monthrange(year, month)[1]
    
    month_sheet = []
    delivery_days_count = 0
    unique_products = set()
    total_month_spent = 0.0
    
    for day_num in range(1, num_days + 1):
        date_obj = datetime(year, month, day_num)
        day_name = date_obj.strftime('%a') # Mon, Tue...
        
        # Check which orders apply to this day
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
                    unique_products.add(item.product.name if item.product else "Unknown")
                    total_month_spent += (item.price * item.quantity)
        
        if day_deliveries:
            delivery_days_count += 1
            month_sheet.append({
                'date': date_obj.strftime('%d %b'),
                'day': date_obj.strftime('%A'),
                'deliveries': day_deliveries,
                'is_past': date_obj.date() < now.date(),
                'is_today': date_obj.date() == now.date()
            })

    stats = {
        'month_name': month_name,
        'total_delivery_days': delivery_days_count,
        'ordered_products': list(unique_products),
        'total_spent': total_month_spent,
        'month_sheet': month_sheet,
        'active_subscriptions': active_orders
    }
    
    return render_template('profile.html', user=current_user, stats=stats)


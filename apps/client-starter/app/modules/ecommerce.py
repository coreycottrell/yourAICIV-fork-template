"""
E-commerce Module
=================
Products, orders, cart, checkout flow, order management.
Toggleable via config: modules.ecommerce

Checkout hands the order to the ACTIVE payment provider
(config.payment.active_provider, Stripe by default) via
modules.payments.get_payment_provider(). Prices are ALWAYS recomputed from
the products table at checkout; the session cart holds only
product_id / variant / qty (plus display snapshots that are never trusted).
"""

import os
import sys
import json
import uuid
import secrets
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, g, jsonify, abort, session)

ecommerce_bp = Blueprint('ecommerce', __name__,
                         template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

ECOMMERCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    compare_price REAL,
    description TEXT,
    short_description TEXT,
    category TEXT DEFAULT 'general',
    image TEXT,
    images TEXT DEFAULT '[]',
    in_stock INTEGER DEFAULT 1,
    featured INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    variants TEXT DEFAULT '[]',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_name TEXT,
    customer_email TEXT,
    customer_phone TEXT,
    shipping_address TEXT,
    items TEXT NOT NULL,
    subtotal REAL NOT NULL,
    shipping REAL DEFAULT 0,
    tax REAL DEFAULT 0,
    total REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_method TEXT,
    payment_ref TEXT,
    access_token TEXT,
    notes TEXT,
    tracking_number TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS testimonials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER DEFAULT 5,
    featured INTEGER DEFAULT 0,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
"""


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _get_app_helpers():
    from flask import current_app
    return current_app.config['_helpers']


def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _is_admin():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── Cart helpers ────────────────────────────────────────────────────────

MAX_QTY_PER_LINE = 99
MAX_CART_LINES = 50


class BadQuantity(ValueError):
    pass


def parse_qty(raw, allow_zero=False):
    """Integer quantity in 1..99 (0 allowed for cart updates = remove)."""
    try:
        qty = int(str(raw).strip())
    except (TypeError, ValueError):
        raise BadQuantity("Quantity must be a whole number.")
    low = 0 if allow_zero else 1
    if qty < low:
        raise BadQuantity("Quantity must be at least 1.")
    return min(qty, MAX_QTY_PER_LINE)


def get_cart():
    return session.get('cart', [])


def _safe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def cart_count():
    return sum(max(0, _safe_int(item.get('qty', 1))) for item in get_cart())


def cart_total():
    """Display-only estimate from the session snapshot. Checkout never uses it."""
    return sum(float(item.get('price', 0) or 0) * max(0, _safe_int(item.get('qty', 1)))
               for item in get_cart())


def price_cart(db, cart):
    """Re-price the cart from the products table.

    Returns (lines, subtotal, errors). A line with a missing or out-of-stock
    product, or a quantity outside 1..99, is an error: the order is refused.
    """
    lines, errors = [], []
    for item in cart:
        qty = _safe_int(item.get('qty'))
        product = db.execute(
            "SELECT id, name, price, image, in_stock FROM products WHERE id = ?",
            (str(item.get('product_id', '')),)).fetchone()
        if not product:
            errors.append('An item in your cart is no longer available.')
            continue
        if not product['in_stock']:
            errors.append(f'{product["name"]} is out of stock.')
            continue
        if qty < 1 or qty > MAX_QTY_PER_LINE:
            errors.append(f'Invalid quantity for {product["name"]}.')
            continue
        price = round(float(product['price']), 2)
        if price < 0:
            errors.append(f'{product["name"]} has an invalid price.')
            continue
        lines.append({
            'product_id': product['id'],
            'name': product['name'],
            'price': price,
            'image': product['image'],
            'variant': str(item.get('variant', ''))[:100],
            'qty': qty,
        })
    subtotal = round(sum(l['price'] * l['qty'] for l in lines), 2)
    return lines, subtotal, errors


@ecommerce_bp.app_context_processor
def inject_cart():
    """Make cart_count and cart_total available to all templates."""
    return dict(cart_count=cart_count(), cart_total=cart_total())


# ── Public: Store ───────────────────────────────────────────────────────

@ecommerce_bp.route('/store')
def store():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    category = request.args.get('category', '')
    if category:
        products = db.execute(
            "SELECT * FROM products WHERE in_stock = 1 AND category = ? "
            "ORDER BY sort_order", (category,)
        ).fetchall()
    else:
        products = db.execute(
            "SELECT * FROM products WHERE in_stock = 1 ORDER BY sort_order"
        ).fetchall()
    categories = db.execute(
        "SELECT DISTINCT category FROM products WHERE in_stock = 1 ORDER BY category"
    ).fetchall()
    return render_template('public/store.html',
                           products=products, categories=categories,
                           current_category=category)


@ecommerce_bp.route('/product/<slug>')
def product_detail(slug):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    product = db.execute(
        "SELECT * FROM products WHERE slug = ?", (slug,)
    ).fetchone()
    if not product:
        abort(404)
    related = db.execute(
        "SELECT * FROM products WHERE category = ? AND id != ? AND in_stock = 1 "
        "ORDER BY sort_order LIMIT 3",
        (product['category'], product['id'])
    ).fetchall()
    return render_template('public/product_detail.html',
                           product=product, related=related, json=json)


# ── Cart routes ─────────────────────────────────────────────────────────

def _rate_limited(max_attempts=30, window=60):
    from flask import current_app
    fn = current_app.config.get('_rate_limited')
    return bool(fn and fn(request.remote_addr, window=window,
                          max_attempts=max_attempts))


def _cart_page(status=200):
    helpers = _get_app_helpers()
    lines, subtotal, errors = price_cart(helpers['get_db'](), get_cart())
    for e in errors:
        flash(e, 'error')
    return render_template('public/cart.html', cart=get_cart(),
                           computed_total=subtotal), status


@ecommerce_bp.route('/cart')
def cart():
    return _cart_page()


@ecommerce_bp.route('/cart/add', methods=['POST'])
def cart_add():
    if _rate_limited():
        abort(429)
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    product_id = request.form.get('product_id', '')
    variant = request.form.get('variant', '')[:100]
    try:
        qty = parse_qty(request.form.get('qty', 1))
    except BadQuantity as e:
        flash(str(e), 'error')
        return _cart_page(400)

    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('ecommerce.store'))
    if not product['in_stock']:
        flash(f'{product["name"]} is out of stock.', 'error')
        return redirect(url_for('ecommerce.store'))

    cart = get_cart()
    # Check if already in cart
    for item in cart:
        if item['product_id'] == product_id and item.get('variant', '') == variant:
            item['qty'] = min(max(1, _safe_int(item.get('qty'))) + qty,
                              MAX_QTY_PER_LINE)
            session['cart'] = cart
            flash(f'{product["name"]} quantity updated.', 'success')
            return redirect(url_for('ecommerce.cart'))
    if len(cart) >= MAX_CART_LINES:
        flash('Your cart is full.', 'error')
        return redirect(url_for('ecommerce.cart'))

    cart.append({
        'product_id': product_id,
        'name': product['name'],
        'price': product['price'],
        'image': product['image'],
        'variant': variant,
        'qty': qty,
    })
    session['cart'] = cart
    flash(f'{product["name"]} added to cart.', 'success')
    return redirect(url_for('ecommerce.cart'))


@ecommerce_bp.route('/cart/update', methods=['POST'])
def cart_update():
    cart = get_cart()
    for i, item in enumerate(cart):
        qty_key = f'qty_{i}'
        new_qty = request.form.get(qty_key)
        if new_qty is not None:
            try:
                cart[i]['qty'] = parse_qty(new_qty, allow_zero=True)
            except BadQuantity as e:
                flash(str(e), 'error')
                return _cart_page(400)
    cart = [item for item in cart if _safe_int(item.get('qty')) > 0]
    session['cart'] = cart
    flash('Cart updated.', 'success')
    return redirect(url_for('ecommerce.cart'))


@ecommerce_bp.route('/cart/remove/<int:index>', methods=['POST'])
def cart_remove(index):
    cart = get_cart()
    if 0 <= index < len(cart):
        removed = cart.pop(index)
        session['cart'] = cart
        flash(f'{removed["name"]} removed from cart.', 'success')
    return redirect(url_for('ecommerce.cart'))


# ── Checkout ────────────────────────────────────────────────────────────

@ecommerce_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('ecommerce.store'))

    helpers = _get_app_helpers()
    db = helpers['get_db']()
    lines, subtotal, errors = price_cart(db, cart)
    if errors or not lines:
        for e in errors or ['Your cart is empty.']:
            flash(e, 'error')
        return redirect(url_for('ecommerce.cart'))

    if request.method == 'POST':
        if _rate_limited(max_attempts=10, window=300):
            abort(429)

        name = request.form.get('name', '').strip()[:200]
        email = request.form.get('email', '').strip()[:254]
        phone = request.form.get('phone', '').strip()[:50]
        address = request.form.get('address', '').strip()[:500]

        if not name or not email or '@' not in email:
            flash('Name and a valid email are required.', 'error')
            return render_template('public/checkout.html', cart=lines,
                                   computed_total=subtotal)
        if subtotal <= 0:
            flash('Order total must be greater than zero.', 'error')
            return redirect(url_for('ecommerce.cart'))

        from modules.payments import get_payment_provider
        provider_name, provider = get_payment_provider(with_name=True)

        order_id = str(uuid.uuid4())
        access_token = secrets.token_urlsafe(32)
        db.execute(
            """INSERT INTO orders
               (id, customer_name, customer_email, customer_phone,
                shipping_address, items, subtotal, total, status,
                payment_method, access_token, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)""",
            (order_id, name, email, phone, address, json.dumps(lines),
             subtotal, subtotal, provider_name, access_token, now_iso()))
        db.commit()

        base = helpers['base_url']()
        result = provider.initiate_payment(
            order_id, int(round(subtotal * 100)),
            metadata={'description': f"Order {order_id[:8]}",
                      'customer_email': email},
            success_url=f"{base}/order/{order_id}?token={access_token}",
            cancel_url=f"{base}/cart")

        if result.get('status') == 'error':
            # Provider detail goes to the log, never to the buyer.
            sys.stderr.write(f"[CHECKOUT] payment init failed for {order_id}: "
                             f"{result.get('message')}\n")
            db.execute("UPDATE orders SET status = 'payment_error' WHERE id = ?",
                       (order_id,))
            db.commit()
            flash('We could not start the payment. You have not been charged. '
                  'Please try again shortly or contact us.', 'error')
            return redirect(url_for('ecommerce.cart'))

        if result.get('payment_ref'):
            db.execute("UPDATE orders SET payment_ref = ? WHERE id = ?",
                       (result['payment_ref'], order_id))
            db.commit()

        # CRM sync (public form: creates a contact, never overwrites one)
        sync = helpers.get('sync_to_crm')
        if sync:
            sync({'first_name': name.split()[0] if name else '',
                  'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                  'email': email, 'phone': phone}, 'order')

        # Owner alert: plain text (no parse_mode), buyer text inert;
        # fire-and-forget, so a Telegram outage never slows checkout.
        items_desc = ', '.join(f"{l['name']} x{l['qty']}" for l in lines)
        helpers['notify_owner'](
            f"New order #{order_id[:8]}: {name} ({email}) -- ${subtotal:.2f} "
            f"({provider_name})\nItems: {items_desc}", event="order")

        session.pop('cart', None)
        if result.get('status') == 'redirect' and result.get('redirect_url'):
            return redirect(result['redirect_url'], code=303)
        flash('Order placed successfully!', 'success')
        # Same browser: grant the view through the session, so the access
        # token never appears in this browser's address bar or history.
        _grant_order_view(order_id)
        return redirect(url_for('ecommerce.order_confirmation',
                                order_id=order_id), code=303)

    return render_template('public/checkout.html', cart=lines,
                           computed_total=subtotal)


# ── Order confirmation: capability URL -> session ───────────────────────
#
# Stripe can only return the buyer to a URL, so the success_url carries the
# order's access token (<base>/order/<id>?token=...). A token in a URL leaks
# through the Referer header, browser history, and copy-paste. So:
#   1. /order/<id>?token=T with a valid T records the order id in the signed,
#      HttpOnly session cookie and 303-redirects to /order/<id> (no token).
#      Redirects are not kept in history, so only the clean URL is.
#   2. /order/<id> without a token renders only for a session that holds that
#      id (or an admin session).
#   3. Every response on this route sends Referrer-Policy: no-referrer and
#      Cache-Control: no-store, so neither URL is ever sent to a third party
#      or cached.
# The token stays valid as the entry point (a buyer who returns in another
# browser follows the Stripe link again); it is compared in constant time.

_ORDER_VIEWS_KEY = 'order_views'
_ORDER_VIEWS_MAX = 10


def _grant_order_view(order_id):
    ids = [i for i in session.get(_ORDER_VIEWS_KEY, []) if i != order_id]
    ids.append(order_id)
    session[_ORDER_VIEWS_KEY] = ids[-_ORDER_VIEWS_MAX:]


@ecommerce_bp.after_request
def _order_page_no_referrer(response):
    if request.endpoint == 'ecommerce.order_confirmation':
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
    return response


@ecommerce_bp.route('/order/<order_id>')
def order_confirmation(order_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    order = db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if not order:
        abort(404)

    provided_token = request.args.get('token')
    if provided_token is not None:
        import hmac as _hmac_mod
        stored_token = order['access_token'] if 'access_token' in order.keys() else ''
        if not provided_token or not stored_token or \
                not _hmac_mod.compare_digest(provided_token, stored_token):
            abort(403)
        _grant_order_view(order_id)
        return redirect(url_for('ecommerce.order_confirmation',
                                order_id=order_id), code=303)

    # M5: only the buyer's session (granted above) or an admin may view.
    if not _is_admin() and order_id not in session.get(_ORDER_VIEWS_KEY, []):
        abort(403)

    return render_template('public/order_confirmation.html',
                           order=order, json=json)


# ── Admin: Products ─────────────────────────────────────────────────────

@ecommerce_bp.route('/admin/products')
@_admin_required
def admin_products():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    products = db.execute(
        "SELECT * FROM products ORDER BY sort_order"
    ).fetchall()
    return render_template('admin/products.html', products=products)


@ecommerce_bp.route('/admin/products/new', methods=['GET', 'POST'])
@_admin_required
def admin_product_new():
    if request.method == 'POST':
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        product_id = request.form.get('id', '').strip()
        if not product_id:
            product_id = str(uuid.uuid4())[:8]
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        if not name or not slug:
            flash('Name and slug are required.', 'error')
            return render_template('admin/product_edit.html', product=None)

        existing = db.execute(
            "SELECT id FROM products WHERE slug = ?", (slug,)
        ).fetchone()
        if existing:
            flash('A product with that slug already exists.', 'error')
            return render_template('admin/product_edit.html', product=None)

        db.execute(
            """INSERT INTO products
               (id, name, slug, price, description, short_description,
                category, in_stock, featured, sort_order, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, name, slug,
             float(request.form.get('price', 0)),
             request.form.get('description', ''),
             request.form.get('short_description', ''),
             request.form.get('category', 'general'),
             1 if request.form.get('in_stock') else 0,
             1 if request.form.get('featured') else 0,
             int(request.form.get('sort_order', 0)),
             now_iso(), now_iso()))
        db.commit()
        flash('Product created!', 'success')
        return redirect(url_for('ecommerce.admin_products'))

    return render_template('admin/product_edit.html', product=None)


@ecommerce_bp.route('/admin/products/<product_id>/edit', methods=['GET', 'POST'])
@_admin_required
def admin_product_edit(product_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    product = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not product:
        abort(404)

    if request.method == 'POST':
        db.execute(
            """UPDATE products SET name=?, price=?, description=?,
               short_description=?, category=?,
               in_stock=?, featured=?, sort_order=?, updated_at=?
               WHERE id=?""",
            (request.form.get('name'),
             float(request.form.get('price', 0)),
             request.form.get('description'),
             request.form.get('short_description'),
             request.form.get('category'),
             1 if request.form.get('in_stock') else 0,
             1 if request.form.get('featured') else 0,
             int(request.form.get('sort_order', 0)),
             now_iso(), product_id))
        db.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('ecommerce.admin_products'))

    return render_template('admin/product_edit.html', product=product)


@ecommerce_bp.route('/admin/products/<product_id>/delete', methods=['POST'])
@_admin_required
def admin_product_delete(product_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('ecommerce.admin_products'))


# ── Admin: Orders ───────────────────────────────────────────────────────

@ecommerce_bp.route('/admin/orders')
@_admin_required
def admin_orders():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC"
    ).fetchall()
    return render_template('admin/orders.html', orders=orders, json=json)


@ecommerce_bp.route('/admin/orders/<order_id>')
@_admin_required
def admin_order_detail(order_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    order = db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if not order:
        abort(404)
    return render_template('admin/order_detail.html', order=order, json=json)


@ecommerce_bp.route('/admin/orders/<order_id>/status', methods=['POST'])
@_admin_required
def admin_order_status(order_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    status = request.form.get('status', 'pending')
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    flash(f'Order status updated to {status}.', 'success')
    return redirect(url_for('ecommerce.admin_order_detail', order_id=order_id))


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    return [
        {'divider': True},
        {'label': 'Products', 'endpoint': 'ecommerce.admin_products',
         'match': 'ecommerce.admin_product'},
        {'label': 'Orders', 'endpoint': 'ecommerce.admin_orders',
         'match': 'ecommerce.admin_order'},
    ]


def get_metrics(db):
    metrics = []
    product_count = db.execute(
        "SELECT COUNT(*) as c FROM products"
    ).fetchone()['c']
    metrics.append({'label': 'Products', 'value': product_count})

    order_count = db.execute(
        "SELECT COUNT(*) as c FROM orders"
    ).fetchone()['c']
    metrics.append({'label': 'Orders', 'value': order_count})

    pending = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE status = 'pending'"
    ).fetchone()['c']
    if pending:
        metrics.append({'label': 'Pending Orders', 'value': pending})

    return metrics


def get_schema():
    return ECOMMERCE_SCHEMA

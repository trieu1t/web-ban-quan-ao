from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-change-me')

DATA_PATH = os.path.join(app.root_path, 'data', 'products.json')
ORDERS_DB = os.path.join(app.root_path, 'data', 'orders.db')


def load_products():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values()) if isinstance(cart, dict) else 0
    return {'cart_count': count}


def get_product_by_id(pid):
    products = load_products()
    return next((p for p in products if p['id'] == pid), None)


def init_db():
    """Initialize the orders SQLite database and create table if needed."""
    os.makedirs(os.path.dirname(ORDERS_DB), exist_ok=True)
    conn = sqlite3.connect(ORDERS_DB)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            address TEXT,
            items_json TEXT,
            total REAL
        )
    ''')
    conn.commit()
    conn.close()


def save_order(customer_name, customer_email, address, items, total):
    """Persist an order and return the new order id."""
    conn = sqlite3.connect(ORDERS_DB)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    items_json = json.dumps(items, ensure_ascii=False)
    cur.execute(
        'INSERT INTO orders (created, customer_name, customer_email, address, items_json, total) VALUES (?, ?, ?, ?, ?, ?)',
        (now, customer_name, customer_email, address, items_json, float(total))
    )
    oid = cur.lastrowid
    conn.commit()
    conn.close()
    return oid


def load_orders(limit=100):
    conn = sqlite3.connect(ORDERS_DB)
    cur = conn.cursor()
    cur.execute('SELECT id, created, customer_name, customer_email, address, items_json, total FROM orders ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    orders = []
    for r in rows:
        orders.append({
            'id': r[0],
            'created': r[1],
            'customer_name': r[2],
            'customer_email': r[3],
            'address': r[4],
            'items': json.loads(r[5]) if r[5] else [],
            'total': r[6]
        })
    return orders


@app.route('/')
def index():
    products = load_products()
    return render_template('index.html', products=products)


@app.route('/product/<int:pid>')
def product(pid):
    products = load_products()
    prod = next((p for p in products if p['id'] == pid), None)
    if not prod:
        return "Product not found", 404
    return render_template('product.html', product=prod)


@app.route('/api/products')
def api_products():
    return jsonify(load_products())


@app.route('/cart')
def cart_view():
    cart = session.get('cart', {})
    products = load_products()
    items = []
    total = 0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except Exception:
            continue
        prod = next((p for p in products if p['id'] == pid), None)
        if prod:
            subtotal = prod['price'] * qty
            total += subtotal
            items.append({'product': prod, 'qty': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/add/<int:pid>', methods=['POST'])
def cart_add(pid):
    prod = get_product_by_id(pid)
    if not prod:
        return jsonify({'ok': False, 'error': 'Product not found'}), 404
    cart = session.get('cart', {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    session['cart'] = cart
    return jsonify({'ok': True, 'cart_count': sum(cart.values())})


@app.route('/cart/update', methods=['POST'])
def cart_update():
    data = request.json or {}
    cart = session.get('cart', {})
    for k, v in data.items():
        if v <= 0:
            cart.pop(str(k), None)
        else:
            cart[str(k)] = int(v)
    session['cart'] = cart
    return jsonify({'ok': True, 'cart_count': sum(cart.values())})


@app.route('/cart/clear')
def cart_clear():
    session.pop('cart', None)
    return redirect(url_for('index'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    products = load_products()
    items = []
    total = 0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except Exception:
            continue
        prod = next((p for p in products if p['id'] == pid), None)
        if prod:
            subtotal = prod['price'] * qty
            total += subtotal
            items.append({'product': prod, 'qty': qty, 'subtotal': subtotal})

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        # Build a simple serializable items structure
        serial_items = [{'id': it['product']['id'], 'name': it['product']['name'], 'qty': it['qty'], 'price': it['product']['price']} for it in items]
        order_id = save_order(name, email, address, serial_items, total)
        # clear cart
        session.pop('cart', None)
        return redirect(url_for('order_confirm', oid=order_id))

    return render_template('checkout.html', items=items, total=total)


@app.route('/order/<int:oid>')
def order_confirm(oid):
    orders = load_orders(limit=1)
    # naive fetch: try to find the order by id in recent orders
    order = next((o for o in orders if o['id'] == oid), None)
    if not order:
        # fallback: fetch directly
        conn = sqlite3.connect(ORDERS_DB)
        cur = conn.cursor()
        cur.execute('SELECT id, created, customer_name, customer_email, address, items_json, total FROM orders WHERE id = ?', (oid,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return 'Order not found', 404
        order = {
            'id': r[0],
            'created': r[1],
            'customer_name': r[2],
            'customer_email': r[3],
            'address': r[4],
            'items': json.loads(r[5]) if r[5] else [],
            'total': r[6]
        }
    return render_template('order.html', order=order)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    products = load_products()
    orders = load_orders(limit=200)
    message = ''
    if request.method == 'POST':
        # Add a new product
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price') or 0)
        image = request.form.get('image', '').strip() or '/static/img/placeholder.jpg'
        if name:
            next_id = max([p['id'] for p in products]) + 1 if products else 1
            products.append({'id': next_id, 'name': name, 'price': price, 'image': image, 'description': ''})
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            message = 'Product added.'
    return render_template('admin.html', products=products, orders=orders, message=message)


@app.route('/admin/delete/<int:pid>', methods=['POST'])
def admin_delete(pid):
    products = load_products()
    products = [p for p in products if p['id'] != pid]
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)

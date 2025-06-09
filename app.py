from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DB_NAME = 'membership.db'
user_cart = {}  # 簡單購物車示範用，實務請用 session 或資料庫

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS members (
                iid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT,
                birthdate TEXT
            )
        ''')
        conn.commit()
        conn.close()

init_db()

products = [
    {'id': 1, 'name': '蘋果', 'price': 50},
    {'id': 2, 'name': '芒果', 'price': 60},
    {'id': 3, 'name': '芭樂', 'price': 50},
    {'id': 4, 'name': '木瓜', 'price': 60},
    {'id': 5, 'name': '鳳梨', 'price': 60},
    {'id': 6, 'name': '西瓜', 'price': 100},
    {'id': 7, 'name': '奇異果', 'price': 30},
    {'id': 8, 'name': '百香果', 'price': 30},
    {'id': 9, 'name': '火龍果', 'price': 60},
    {'id': 10, 'name': '水蜜桃', 'price': 60}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        birthdate = request.form.get('birthdate')

        if not username or not email or not password:
            return render_template('register.html', error='請填寫用戶名、電子郵件和密碼')

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT * FROM members WHERE username = ? OR email = ?', (username, email))
        if c.fetchone():
            conn.close()
            return render_template('register.html', error='用戶名或電子郵件已被使用')

        c.execute('INSERT INTO members (username, email, password, phone, birthdate) VALUES (?, ?, ?, ?, ?)',
                  (username, email, password, phone, birthdate))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template('login.html', error='請輸入電子郵件和密碼')

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT iid, username FROM members WHERE email = ? AND password = ?', (email, password))
        result = c.fetchone()
        conn.close()

        if result:
            iid, username = result
            user_cart[iid] = {}  # 初始化購物車
            return render_template('welcome.html', username=username, iid=iid)
        else:
            return render_template('login.html', error='電子郵件或密碼錯誤')

    return render_template('login.html')

@app.route('/shop/<int:iid>')
def shop(iid):
    if iid not in user_cart:
        return redirect(url_for('login'))
    return render_template('shop.html', products=products, iid=iid)

@app.route('/add_to_cart/<int:iid>/<int:product_id>')
def add_to_cart(iid, product_id):
    if iid not in user_cart:
        return redirect(url_for('login'))
    cart = user_cart[iid]
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    return redirect(url_for('cart', iid=iid))

@app.route('/cart/<int:iid>', methods=['GET', 'POST'])
def cart(iid):
    if iid not in user_cart:
        return redirect(url_for('login'))
    cart = user_cart[iid]

    if request.method == 'POST':
        for pid in list(cart.keys()):
            qty = request.form.get(f'qty_{pid}')
            if qty and qty.isdigit():
                qty_int = int(qty)
                if qty_int <= 0:
                    cart.pop(pid)
                else:
                    cart[pid] = qty_int
        return redirect(url_for('checkout', iid=iid))

    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in products if p['id'] == int(pid)), None)
        if product:
            subtotal = product['price'] * qty
            total += subtotal
            cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': qty,
                'subtotal': subtotal,
            })
    return render_template('cart.html', cart_items=cart_items, total=total, iid=iid)

@app.route('/checkout/<int:iid>')
def checkout(iid):
    if iid not in user_cart:
        return redirect(url_for('login'))
    cart = user_cart[iid]

    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in products if p['id'] == int(pid)), None)
        if product:
            subtotal = product['price'] * qty
            total += subtotal
            cart_items.append({
                'name': product['name'],
                'quantity': qty,
                'price': product['price'],
                'subtotal': subtotal,
            })

    return render_template('checkout.html', cart_items=cart_items, total=total, iid=iid)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from models import db, User
from config import Config
import psycopg2
from nsetools import Nse

app = Flask(__name__)
app.config.from_object(Config)

# --- Ensure 'algotrade' database exists ---
def ensure_database():
    # Connect to default 'postgres' database
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='passig',
        host='localhost'
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname='algotrade'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('CREATE DATABASE algotrade')
    cur.close()
    conn.close()

ensure_database()

# Now switch SQLAlchemy to use 'algotrade'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:passig@localhost/algotrade'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter((User.username==email_or_username) | (User.email==email_or_username)).first()
        if user and user.password == password:
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Check if user exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists')
            return render_template('signup.html')
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    nse = Nse()
    stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    stock_data = []
    for symbol in stocks:
        try:
            q = nse.get_quote(symbol)
            # Debug: print the raw response to console
            print(f"{symbol} quote: {q}")
            company = q.get('companyName') or q.get('symbol', symbol)
            price = q.get('lastPrice') or q.get('last_price') or 'N/A'
            change = q.get('change') or q.get('netPrice') or 'N/A'
            percentChange = q.get('pChange') or q.get('perChange') or 'N/A'
            # Convert price to float if possible
            if isinstance(price, str):
                price = price.replace(',', '').replace('₹', '').strip()
                try:
                    price = float(price)
                except Exception:
                    price = 'N/A'
            if isinstance(change, str):
                change = change.replace(',', '').replace('₹', '').strip()
                try:
                    change = float(change)
                except Exception:
                    change = 'N/A'
            if isinstance(percentChange, str):
                percentChange = percentChange.replace('%', '').strip()
                try:
                    percentChange = float(percentChange)
                except Exception:
                    percentChange = 'N/A'
            stock_data.append({
                'symbol': symbol,
                'company': company,
                'price': price,
                'change': change,
                'percentChange': percentChange
            })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            stock_data.append({
                'symbol': symbol,
                'company': symbol,
                'price': 'N/A',
                'change': 'N/A',
                'percentChange': 'N/A'
            })
    # Check if all prices are N/A and set a flag
    all_na = all(s['price'] == 'N/A' for s in stock_data)
    return render_template('dashboard.html', stock_data=stock_data, all_na=all_na)

@app.route('/create_test_user')
def create_test_user():
    # Only create if not exists
    if not User.query.filter_by(username='testuser').first():
        user = User(username='testuser', email='test@example.com', password='testpass')
        db.session.add(user)
        db.session.commit()
        return "Test user created: username='testuser', password='testpass'"
    return "Test user already exists."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

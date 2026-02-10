from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Avoid scrypt on systems where hashlib.scrypt is unavailable
PASSWORD_HASH_METHOD = 'pbkdf2:sha256'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='assigned_user', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='client', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(30), unique=True, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120))
    client_company = db.Column(db.String(100))
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    items_json = db.Column(db.Text, nullable=False)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_rate = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='invoices', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def items(self):
        try:
            return json.loads(self.items_json)
        except Exception:
            return []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        users = User.query.filter_by(is_admin=False).count()
        clients = Client.query.count()
        tasks = Task.query.count()
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
        return render_template('admin_dashboard.html', users=users, clients=clients, tasks=tasks, recent_tasks=recent_tasks)
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        return render_template('user_dashboard.html', tasks=tasks)

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('users'))
    
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password, method=PASSWORD_HASH_METHOD),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    flash('User added successfully', 'success')
    return redirect(url_for('users'))

@app.route('/users/delete/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot delete admin user', 'danger')
        return redirect(url_for('users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('users'))

@app.route('/clients')
@login_required
def clients():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/invoices')
@login_required
def invoices():
    if current_user.is_admin:
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    else:
        invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    if request.method == 'POST':
        client_name = request.form.get('client_name', '').strip()
        client_email = request.form.get('client_email', '').strip()
        client_company = request.form.get('client_company', '').strip()
        due_date_raw = request.form.get('due_date')
        notes = request.form.get('notes', '').strip()
        tax_rate_raw = request.form.get('tax_rate', '0').strip()

        if not client_name:
            flash('Client name is required', 'danger')
            return redirect(url_for('new_invoice'))

        items = []
        descriptions = request.form.getlist('item_description')
        quantities = request.form.getlist('item_quantity')
        prices = request.form.getlist('item_price')
        for desc, qty, price in zip(descriptions, quantities, prices):
            desc = (desc or '').strip()
            if not desc:
                continue
            try:
                qty_val = float(qty) if qty else 0.0
                price_val = float(price) if price else 0.0
            except ValueError:
                qty_val = 0.0
                price_val = 0.0
            if qty_val <= 0 or price_val < 0:
                continue
            items.append({
                'description': desc,
                'quantity': qty_val,
                'unit_price': price_val,
                'line_total': round(qty_val * price_val, 2),
            })

        if not items:
            flash('Add at least one invoice item', 'danger')
            return redirect(url_for('new_invoice'))

        try:
            tax_rate = float(tax_rate_raw) if tax_rate_raw else 0.0
        except ValueError:
            tax_rate = 0.0

        subtotal = round(sum(item['line_total'] for item in items), 2)
        tax_amount = round(subtotal * (tax_rate / 100.0), 2)
        total = round(subtotal + tax_amount, 2)

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, '%Y-%m-%d')
            except ValueError:
                due_date = None

        prefix = datetime.utcnow().strftime('%Y%m%d')
        count_today = Invoice.query.filter(Invoice.number.like(f'INV-{prefix}-%')).count() + 1
        number = f'INV-{prefix}-{count_today:04d}'

        invoice = Invoice(
            number=number,
            client_name=client_name,
            client_email=client_email,
            client_company=client_company,
            due_date=due_date,
            notes=notes,
            items_json=json.dumps(items),
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=total,
            user_id=current_user.id,
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Invoice generated', 'success')
        return redirect(url_for('view_invoice', id=invoice.id))

    return render_template('invoice_new.html')

@app.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    if not current_user.is_admin and invoice.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    return render_template('invoice_view.html', invoice=invoice, items=invoice.items())

@app.route('/clients/add', methods=['POST'])
@login_required
def add_client():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    client = Client(
        name=request.form.get('name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        company=request.form.get('company')
    )
    db.session.add(client)
    db.session.commit()
    flash('Client added successfully', 'success')
    return redirect(url_for('clients'))

@app.route('/clients/delete/<int:id>')
@login_required
def delete_client(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully', 'success')
    return redirect(url_for('clients'))

@app.route('/tasks')
@login_required
def tasks():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    tasks = Task.query.all()
    users = User.query.filter_by(is_admin=False).all()
    clients = Client.query.all()
    return render_template('tasks.html', tasks=tasks, users=users, clients=clients)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    task = Task(
        title=request.form.get('title'),
        description=request.form.get('description'),
        status=request.form.get('status', 'pending'),
        priority=request.form.get('priority', 'medium'),
        due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None,
        user_id=request.form.get('user_id'),
        client_id=request.form.get('client_id')
    )
    db.session.add(task)
    db.session.commit()
    flash('Task assigned successfully', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/update/<int:id>', methods=['POST'])
@login_required
def update_task(id):
    task = Task.query.get_or_404(id)
    if not current_user.is_admin and task.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    task.status = request.form.get('status', task.status)
    db.session.commit()
    flash('Task updated successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tasks/delete/<int:id>')
@login_required
def delete_task(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully', 'success')
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@crm.com',
                password=generate_password_hash('admin123', method=PASSWORD_HASH_METHOD),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=5001)

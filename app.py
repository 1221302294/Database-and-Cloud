from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
db = SQLAlchemy(app)

# Database model for Employee
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)

# Admin credentials (for simplicity, stored in code; use a secure method in production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

with app.app_context():
    db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        return redirect(url_for('index'))
    return "Invalid credentials", 403

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def index():
    if not session.get('admin'):
        return redirect(url_for('login'))
    employees = Employee.query.all()
    return render_template('index.html', employees=employees)

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        new_employee = Employee(name=name, position=position)
        db.session.add(new_employee)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/delete/<int:employee_id>')
def delete_employee(employee_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    employee = Employee.query.get(employee_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    employee = Employee.query.get(employee_id)
    if not employee:
        return "Employee not found", 404

    if request.method == 'POST':
        employee.name = request.form['name']
        employee.position = request.form['position']
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', employee=employee)

if __name__ == '__main__':
    app.run(debug=True)

import logging
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import bcrypt
from forms import EmployeeForm

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Tan5346!@localhost:3306/Assignment1'

db = SQLAlchemy(app)

# Configure audit logging
logging.basicConfig(
    filename='audit.log',           # File to save logs
    level=logging.INFO,             # Log level
    format='%(asctime)s - %(message)s',  # Log format (includes timestamp)
    filemode='a'                    # Append mode to avoid overwriting
)

# Database model for Employee
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
# Admin credentials (for simplicity, stored in code; use a secure method in production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']

    # Admin login
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin'] = True
        logging.info(f"Admin logged in successfully.")
        return redirect(url_for('index'))

    # Employee login
    employee = Employee.query.filter_by(name=username).first()
    if employee and bcrypt.checkpw(password.encode('utf-8'), employee.password.encode('utf-8')):
        session['employee_id'] = employee.id
        logging.info(f"Employee logged in: {username}, ID: {employee.id}")
        return redirect(url_for('employee_dashboard'))

    logging.warning(f"Failed login attempt for username: {username}")
    return "Invalid credentials", 403

@app.route('/logout')
def logout():
    if 'admin' in session:
        logging.info("Admin logged out.")
    elif 'employee_id' in session:
        employee = Employee.query.get(session['employee_id'])
        logging.info(f"Employee logged out: {employee.name}, ID: {employee.id}")
    
    session.pop('admin', None)
    session.pop('employee_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def index():
    if not session.get('admin'):
        return redirect(url_for('login'))
    employees = Employee.query.all()
    return render_template('index.html', employees=employees)

@app.route('/employee-dashboard')
def employee_dashboard():
    if not session.get('employee_id'):
        return redirect(url_for('login'))
    employee = Employee.query.get(session['employee_id'])
    return render_template('employee_dashboard.html', employee=employee)

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if not session.get('admin'):
        return redirect(url_for('login'))

    form = EmployeeForm()
    if form.validate_on_submit():
        name = form.name.data
        position = form.position.data
        password = form.password.data

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save the employee to the database
        new_employee = Employee(name=name, position=position, password=hashed_password)
        db.session.add(new_employee)
        db.session.commit()

        # Log the action to the audit file
        logging.info(f"Admin added new employee: {name}, Position: {position}")

        return redirect(url_for('index'))

    return render_template('add.html', form=form)


@app.route('/delete/<int:employee_id>')
def delete_employee(employee_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    
    # Find the employee by ID
    employee = Employee.query.get(employee_id)
    if employee:
        logging.info(f"Admin deleted employee: {employee.name}, ID: {employee.id}")
        db.session.delete(employee)
        db.session.commit()

    # Check if the table is empty
    if Employee.query.count() == 0:
        # Reset the auto-increment counter using raw SQL wrapped in text()
        db.session.execute(text('ALTER TABLE Employee AUTO_INCREMENT = 1'))
        db.session.commit()
        logging.info("Auto-increment ID reset to 1 as the Employee table is empty.")

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

        # Handle password update
        new_password = request.form['password']
        if new_password:  # If a new password is provided
            if len(new_password) < 6:  # Check minimum length
                return "Password must be at least 6 characters", 400
            
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            employee.password = hashed_password.decode('utf-8')  # Update hashed password

        db.session.commit()
        logging.info(f"Admin updated employee: {employee.name}, ID: {employee.id}")
        return redirect(url_for('index'))

    return render_template('edit.html', employee=employee)


if __name__ == '__main__':
    app.run(debug=True)

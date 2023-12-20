from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename 
from flask_session import Session
from datetime import timedelta
from functools import wraps
import sqlite3
import uuid
import re
import os

UPLOAD_FOLDER = 'uploads' 

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'Secret_key'
app.config['SECRET_KEY'] = 'tryty5568'
app.config['SESSION_TYPE'] = 'filesystem'  # Use server-side storage for sessions
Session(app)
app.permanent_session_lifetime = timedelta(minutes=15)


# Function to create the database and tables if they don't exist
def create_database():
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    
    # User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            unique_id TEXT NOT NULL,
            registration_date TEXT NOT NULL,
            user_role TEXT NOT NULL
        )
    ''')
    
    # Complaint table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaint (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_text TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')

    # Evidence table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            
            evidence_file TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaint (id)
        )
    ''')

    # Authority table
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS authority (
    #         authority_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         name TEXT NOT NULL,
            
    #         unique_id TEXT NOT NULL,
    #         user_id INTEGER NOT NULL,
    #         FOREIGN KEY (user_id) REFERENCES user (user_id)
    #     )
    # ''')

    # Insert the default admin entry
    # cursor.execute('''
    #     INSERT OR IGNORE INTO user (username, password, name, email, unique_id, registration_date, user_role)
    #     VALUES (?, ?, ?, ?, ?, ?, ?)
    # ''', ('admin', 'admin@123', 'Prajjwalkumar', 'prajjwalkumar777@deccansociety.org', '1', '2023-09-03', 'admin'))
    
    conn.commit()
    conn.close()
create_database()



def is_logged_in():
    return 'user_id' in session

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response



@app.route('/')
def home():
    # if 'user_id' in session:
    #     return render_template('home.html')
    # else:
    #     return render_template('login.html')
    return render_template('home.html') 

     

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_role = request.form['user_role']
        
        conn = sqlite3.connect('abuse_reporting.db')
        cursor = conn.cursor()
        sql_query = """SELECT user_id FROM user
                        WHERE username = ? AND password = ? AND user_role = ?;    
        """
        cursor.execute(sql_query, (username, password, user_role))
        user_id = cursor.fetchone()

        conn.close()
        # global user_id 
        # user_id= user[0]
        # print(user_id)
        # Check if the provided username and password is correct

        if user_id:
            session['user_id'] = user_id[0]
        
            if user_role == 'user':
                return redirect(url_for('dashboard'))
            
            elif user_role == 'admin':
                return redirect(url_for('admin_dashboard'))
            
            elif user_role == 'authority':
                return redirect(url_for('authority_dashboard'))
            
            
        else:
                flash(('Invalid username or password. Please try again.', 'error'))
                return redirect(url_for('login'))            
        
        
        
        
    return render_template('login.html')




# Route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        user_role = request.form['user_role']

         # Validate email using regular expression
        if not re.match(r"[a-zA-Z0-9._%+-]+@deccansociety.org", email):
            flash(('Invalid email address. Please use a valid @deccansociety.org email.', 'error'))
            return redirect(url_for('register'))

        # Generate a unique ID
        unique_id = str(uuid.uuid4())
        
        conn = sqlite3.connect('abuse_reporting.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()
        conn.close()

        # Check if the username or email already exists
        if existing_user is not None:
            flash(('Username or email already exists. Please try again.', 'error'))
            return redirect(url_for('register')) 
        
        else:

       
        
            # Check if the user role is authority or admin
            if user_role in ('authority', 'admin'):
                authority_admin_username = request.form['authority_admin_username'] 
                authority_admin_password = request.form['authority_admin_password']

                conn = sqlite3.connect('abuse_reporting.db')
                cursor = conn.cursor()
                sql_query = """SELECT * FROM user
                                WHERE username = ? AND user_role = 'admin' AND password = ?;    
                """

                # Execute the SQL query with placeholders
                cursor.execute(sql_query, (authority_admin_username, authority_admin_password))

                user = cursor.fetchone()
                conn.close()
        
            
                # Check if the provided authority/admin password is correct
                if user:
                    conn = sqlite3.connect('abuse_reporting.db')
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO user (username, password, name, email, unique_id, registration_date, user_role) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)',
                            (username, password, name, email, unique_id, user_role))
                    conn.commit()
                    # Get the auto-generated user ID after insertion
                    user_id = cursor.lastrowid

                    # Store the user ID in the session
                    session['user_id'] = user_id
                    conn.close()    

                else:
                    flash(('Admin password is incorrect. Registration failed.', 'error'))
                    return redirect(url_for('register'))
            
            
                

            else:
                # Insert user data into the database
                conn = sqlite3.connect('abuse_reporting.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO user (username, password, name, email, unique_id, registration_date, user_role) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)',
                            (username, password, name, email, unique_id, user_role))
                conn.commit()
                # Get the auto-generated user ID after insertion
                user_id = cursor.lastrowid

                # Store the user ID in the session
                session['user_id'] = user_id
                

                conn.close()

            flash(('Registration successful! Your unique ID is: {}'.format(unique_id), 'success'))
            return redirect(url_for('login'))

    return render_template('register.html')


#User side 
@app.route('/dashboard', methods=['GET', 'POST'])

def dashboard():
    user_id= session.get('user_id')

    if user_id is None:
        flash('Please log in to view your profile', 'error')
        return redirect('/login')
    
    return render_template('dashboard.html')

@app.route('/make_complaint', methods=['GET'])

def make_complaint_form():
    user_id= session.get('user_id')
    if user_id is None:
        flash('Please log in to view your profile', 'error')
        return redirect('/login')
    print(user_id)
    return render_template('make_complaint.html')



@app.route('/submit_complaint', methods=['POST'])

def submit_complaint():
    # Get the user ID from the session (you need to implement user authentication)
    user_id = session.get('user_id')
    print(user_id)
    

    if user_id is None:
        # Handle the case where the user is not authenticated
        return redirect('/login')  # Redirect to your login page or display an error message

    # Get the form data
    incident_description = request.form.get('incident_description')
    
    evidence_file = request.files.get('evidence')


    # Store the complaint in the complaints table
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO complaint (user_id, complaint_text, status,timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                   (user_id, incident_description, 'Pending'))
    complaint_id = cursor.lastrowid

    # Handle the evidence file if provided
    if evidence_file:
        evidence_filename = secure_filename(evidence_file.filename)
        evidence_file.save(os.path.join(app.config['UPLOAD_FOLDER'], evidence_filename))

        # Store the evidence in the evidence table
        cursor.execute('INSERT INTO evidence (complaint_id, evidence_file) VALUES (?, ?)',
                       (complaint_id,evidence_filename))

    conn.commit()
    conn.close()
    flash('Complaint submitted successfully!', 'success')

    # Redirect the user to a confirmation page or another relevant page
    return render_template('make_complaint.html')





@app.route('/view_complaints', methods=['GET', 'POST'])

def view_complaints():
    user_id = session.get('user_id')
    # user_id = session['user_id']  # Get the user's ID from the session
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, complaint_text, status FROM complaint WHERE user_id = ?', (user_id,))
    complaints = cursor.fetchall()
    conn.close()

    return render_template('view_complaints.html', complaints=complaints)
    #Test code
    # return render_template('view_complaints.html')

@app.route('/profile', methods=['GET', 'POST'])

def profile():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to view your profile', 'error')
        return redirect('/login')

    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, name, email, unique_id FROM user WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, username, name, email, unique_id = user
    else:
        flash('User not found', 'error')
        return redirect('/dashboard')

    return render_template('profile.html', user_id=user_id, username=username, name=name, email=email, unique_id=unique_id)










# Admin section

@app.route('/admin_dashboard')

def admin_dashboard():
    user_id = session.get('user_id')
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    # Establish a database connection
    # user_id= session.get('user_id')
    # if user_id is None:
    #     flash('Please log in to view your profile', 'error')
    #     return redirect('/login')
    
    # conn = sqlite3.connect('abuse_reporting.db')
    # cursor = conn.cursor()

    # # Query for retrieving user data
    # cursor.execute("SELECT user_id, name,user_role FROM user")
    # users = cursor.fetchall()

    # # Close the database connection
    # conn.close()

    # Render the admin dashboard template and pass the user data
    # return render_template('admin_dashboard.html', users=users)
    return render_template('admin_dashboard.html')

@app.route('/view_user')

def view_user():

    user_id = session.get('user_id')
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, email, user_role FROM user")
    users = cursor.fetchall()
    conn.close()
    
    return render_template('view_user.html', users=users)

@app.route('/admin_profile/<int:user_id>')

def view_user_profile(user_id):
    # user_id = session.get('user_id')
    # if user_id is None:
    #     flash('Please log in to view your complaints', 'error')
    #     return redirect('/login')

    # Establish a database connection
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()

    # Query to retrieve user profile information
    cursor.execute("SELECT user_id, name, email,user_role FROM user WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    # Query to retrieve user's complaints and their status
    cursor.execute("SELECT status, complaint_text FROM complaint WHERE user_id = ?", (user_id,))
    complaints = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the user profile template with the retrieved data
    return render_template('user_profile.html', user_data=user_data, complaints=complaints)


@app.route('/admin_profile', methods=['GET', 'POST'])

def admin_profile():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to view your profile', 'error')
        return redirect('/login')

    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, name, email, unique_id FROM user WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, username, name, email, unique_id = user
    else:
        flash('User not found', 'error')
        return redirect('/admin_dashboard')

    return render_template('admin_profile.html', user_id=user_id, username=username, name=name, email=email, unique_id=unique_id)






#Authority section

@app.route('/authority_dashboard')

def authority_dashboard():
    user_id = session.get('user_id')
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    return render_template('authority_dashboard.html')



@app.route('/auth_complaints')

def auth_complaints():
    user_id = session.get('user_id')
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaint")
    complaints = cursor.fetchall()
    conn.close()
    return render_template('auth_complaints.html', complaints=complaints)
    # return render_template('auth_complaints.html')


@app.route('/complaints/update_status/<int:complaint_id>', methods=['POST'])

def update_status(complaint_id):
    user_id = session.get('user_id')
    if user_id is None:
        flash('Please log in to view your complaints', 'error')
        return redirect('/login')
    new_status = request.form.get('status')

    # Update the status of the complaint in the database
    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE complaint SET status = ? WHERE complaint_id = ?", (new_status, complaint_id))
    conn.commit()
    conn.close()
    # Redirect the user to the view_complaints page


    flash('Status updated successfully', 'success')
    return redirect(url_for('auth_complaints'))



@app.route('/auth_profile', methods=['GET', 'POST'])

def auth_profile():
    user_id = session.get('user_id')

    if user_id is None:
        flash('Please log in to view your profile', 'error')
        return redirect('/login')

    conn = sqlite3.connect('abuse_reporting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, name, email, unique_id FROM user WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, username, name, email, unique_id = user
    else:
        flash('User not found', 'error')
        return redirect('/auth_dashboard')

    return render_template('auth_profile.html', user_id=user_id, username=username, name=name, email=email, unique_id=unique_id)




# show entire database
@app.route('/all_entries')
def display_all_entries():
    database_path = 'abuse_reporting.db'  # Replace with your database path
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Retrieve all entries from the 'user' table
    cursor.execute("SELECT * FROM user")
    user_entries = cursor.fetchall()

    cursor.execute("SELECT * FROM complaint")
    comp_entries = cursor.fetchall()

    cursor.execute("SELECT * FROM evidence")
    evid = cursor.fetchall()


    # # Retrieve all entries from the 'authority' table
    # cursor.execute("SELECT * FROM authority")
    # authority_entries = cursor.fetchall()

    conn.close()

    return render_template('all_entries.html', user_entries=user_entries,comp_entries=comp_entries,evidence=evid)

@app.route('/delete_duplicates', methods=['GET', 'POST'])
def delete_duplicates():
    if request.method == 'POST':
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect('abuse_reporting.db')
            cursor = conn.cursor()

            # SQL query to delete duplicate records based on a specific criterion
            # delete_query = """
            #     DELETE FROM user
            #     WHERE user_id NOT IN (
            #         SELECT MIN(user_id)
            #         FROM user
            #         GROUP BY username, email
            #     );
            # """
            delete_query = """DELETE FROM user
            WHERE user_role = 'Admin';"""
            # Execute the delete query
            cursor.execute(delete_query)

            # Commit the changes to the database
            conn.commit()

            # Close the database connection
            conn.close()

            flash('Duplicate records deleted successfully!', 'success')
            return redirect(url_for('home'))  # Redirect to a relevant page

        except sqlite3.Error as e:
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('delete_duplicates.html')  # Create an HTML template for this route


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout successful!', 'success')
    return redirect(url_for('login'))



@app.route('/protected', methods=['GET'])
def protected():
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    return render_template('protected.html')

if __name__ == '__main__':
    app.run(debug=True)

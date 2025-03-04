import os
import psycopg2  # Replaced mysql.connector with psycopg2
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import qrcode
from io import BytesIO
import base64
from pathlib import Path
import requests

# Define SheetDB API URL
SHEETDB_REGISTRATION_URL = "https://sheetdb.io/api/v1/lvg1wuw9n1k20"

# Create the Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=["*"])

# PostgreSQL Configuration for qr_code_attendance (Student Registration)
POSTGRES_HOST_REG = os.getenv("POSTGRES_HOST_REG", "dpg-cv3fhfl6l47c73fd9tm0-a")
POSTGRES_USER_REG = os.getenv("POSTGRES_USER_REG", "qr_database_iu3a_user")
POSTGRES_PASSWORD_REG = os.getenv("POSTGRES_PASSWORD_REG", "bvaaARoWzrTTmBW5uayoTuosDzQwpWBN")
POSTGRES_DATABASE_REG = os.getenv("POSTGRES_DATABASE_REG", "qr_database_iu3a")
POSTGRES_PORT_REG = os.getenv("POSTGRES_PORT_REG", "5432")

# PostgreSQL Configuration for qr_code_attendance_making (Attendance)
POSTGRES_HOST_ATT = os.getenv("POSTGRES_HOST_ATT", "dpg-cv3fhfl6l47c73fd9tm0-a")
POSTGRES_USER_ATT = os.getenv("POSTGRES_USER_ATT", "qr_database_iu3a_user")
POSTGRES_PASSWORD_ATT = os.getenv("POSTGRES_PASSWORD_ATT", "bvaaARoWzrTTmBW5uayoTuosDzQwpWBN")
POSTGRES_DATABASE_ATT = os.getenv("POSTGRES_DATABASE_ATT", "qr_database_iu3a")
POSTGRES_PORT_ATT = os.getenv("POSTGRES_PORT_ATT", "5432")

# Upload Folder Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# Initialize PostgreSQL Database Connection for Student Registration
def get_db_connection_reg():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST_REG,
            user=POSTGRES_USER_REG,
            password=POSTGRES_PASSWORD_REG,
            database=POSTGRES_DATABASE_REG,
            port=POSTGRES_PORT_REG
        )
        print("✅ Connected to PostgreSQL (Registration)!")
        return conn
    except psycopg2.Error as err:
        print("⚠️ PostgreSQL Error (Registration):", err)
        return None

# Initialize PostgreSQL Database Connection for Attendance
def get_db_connection_att():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST_ATT,
            user=POSTGRES_USER_ATT,
            password=POSTGRES_PASSWORD_ATT,
            database=POSTGRES_DATABASE_ATT,
            port=POSTGRES_PORT_ATT
        )
        print("✅ Connected to PostgreSQL (Attendance)!")
        return conn
    except psycopg2.Error as err:
        print("⚠️ PostgreSQL Error (Attendance):", err)
        return None

# Create User-Specific Student Registration Table
def create_user_student_table(username):
    conn = get_db_connection_reg()
    if not conn:
        return False

    cursor = conn.cursor()
    table_name = f"students_{username}"
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            rollNumber VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            father_name VARCHAR(255) NOT NULL,
            mother_name VARCHAR(255) NOT NULL,
            date_of_birth DATE NOT NULL,
            class VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            gender VARCHAR(255) NOT NULL,
            academicYear VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    return True

# Initialize PostgreSQL Databases
def init_db():
    # Initialize Registration Database
    conn_reg = get_db_connection_reg()
    if conn_reg:
        conn_reg.close()
        print("✅ Registration Database initialized!")
    else:
        print("⚠️ Failed to initialize Registration Database.")

    # Initialize Attendance Database
    conn_att = get_db_connection_att()
    if conn_att:
        cursor_att = conn_att.cursor()
        # Create a general attendance table (optional, can be removed if not needed)
        cursor_att.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                rollNumber VARCHAR(255) NOT NULL,
                time VARCHAR(255) NOT NULL,
                date VARCHAR(255) NOT NULL
            )
        ''')
        conn_att.commit()
        conn_att.close()
        print("✅ Attendance Database initialized!")
    else:
        print("⚠️ Failed to initialize Attendance Database.")

init_db()  # Run database setup

# Serve static files (frontend)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Register Student API
@app.route('/register_student', methods=['POST', 'OPTIONS'])
def register_student():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response, 200

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = [
        "username", "rollNumber", "name", "father_name", "mother_name", "date_of_birth",
        "class", "category", "gender", "academicYear"
    ]
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    username = data.get("username")
    rollNumber = data.get("rollNumber")
    name = data.get("name")
    father_name = data.get("father_name")
    mother_name = data.get("mother_name")
    date_of_birth = data.get("date_of_birth")
    classValue = data.get("class")
    category = data.get("category")
    gender = data.get("gender")
    academicYear = data.get("academicYear")

    try:
        if not create_user_student_table(username):
            return jsonify({"error": "Database connection error"}), 500

        conn = get_db_connection_reg()
        if not conn:
            return jsonify({"error": "Database connection error"}), 500

        cursor = conn.cursor()
        table_name = f"students_{username}"
        cursor.execute(
            f"INSERT INTO {table_name} (rollNumber, name, father_name, mother_name, date_of_birth, class, category, gender, academicYear) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (rollNumber, name, father_name, mother_name, date_of_birth, classValue, category, gender, academicYear)
        )
        conn.commit()
        conn.close()

        print(f"✅ Student registered: {rollNumber}, {name}, {father_name}, {mother_name}, {date_of_birth}, {classValue}, {category}, {gender}, {academicYear}")

        response = requests.post(SHEETDB_REGISTRATION_URL, json={"data": [data]})
        print("✅ SheetDB Registration Response:", response.json())

        return jsonify({"message": "Student registration successful"})

    except psycopg2.IntegrityError as e:
        print("⚠️ Integrity Error:", str(e))
        return jsonify({"error": "Student already registered"}), 400
    except psycopg2.Error as e:
        print("⚠️ PostgreSQL Error:", str(e))
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print("⚠️ Server error:", str(e))
        return jsonify({"error": "Server error: Could not register student"}), 500

# Fetch Student Details API
@app.route('/student_details/<username>/<rollNumber>', methods=['GET', 'OPTIONS'])
def student_details(username, rollNumber):
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET")
        return response, 200

    conn = get_db_connection_reg()
    if not conn:
        return jsonify({"error": "Database connection error"}), 500

    cursor = conn.cursor()
    table_name = f"students_{username}"
    cursor.execute(
        f"SELECT * FROM {table_name} WHERE rollNumber = %s",
        (rollNumber,)
    )
    student = cursor.fetchone()
    conn.close()

    if not student:
        return jsonify({"error": "Student not found"}), 404

    # Map database fields to response
    student_data = {
        "rollNumber": student[1],
        "name": student[2],
        "father_name": student[3],
        "mother_name": student[4],
        "date_of_birth": student[5].strftime('%Y-%m-%d'),  # Format date as YYYY-MM-DD
        "class": student[6],
        "category": student[7],
        "gender": student[8],
        "academicYear": student[9]
    }

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(student_data))
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "student": student_data,
        "qr_code": img_str
    })

# Create User-Specific Attendance Table
def create_user_attendance_table(username):
    conn = get_db_connection_att()
    if not conn:
        return False

    cursor = conn.cursor()
    table_name = f"attendance_{username}"
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            rollNumber VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            father_name VARCHAR(255) NOT NULL,
            mother_name VARCHAR(255) NOT NULL,
            date_of_birth DATE NOT NULL,
            class VARCHAR(255) NOT NULL,
            category VARCHAR(255) NOT NULL,
            gender VARCHAR(255) NOT NULL,
            academicYear VARCHAR(255) NOT NULL,
            attendance_month VARCHAR(255) NOT NULL,
            time VARCHAR(255) NOT NULL,
            date VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    return True

# Mark Attendance API
@app.route('/attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    print("Incoming Attendance Data:", data)  # Debugging

    username = data.get("username")
    rollNumber = data.get("rollNumber")
    name = data.get("name")
    father_name = data.get("father_name")
    mother_name = data.get("mother_name")
    date_of_birth = data.get("date_of_birth")
    classValue = data.get("class")
    category = data.get("category")
    gender = data.get("gender")
    academicYear = data.get("academicYear")
    attendance_month = data.get("attendance_month")
    time = data.get("time")
    date = data.get("date")

    try:
        if not create_user_attendance_table(username):
            return jsonify({"error": "Database connection error"}), 500

        conn = get_db_connection_att()
        if not conn:
            return jsonify({"error": "Database connection error"}), 500

        cursor = conn.cursor()
        table_name = f"attendance_{username}"

        # Check if attendance for the same date already exists
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE rollNumber = %s AND date = %s",
            (rollNumber, date)
        )
        existing_attendance = cursor.fetchone()

        if existing_attendance:
            conn.close()
            return jsonify({"error": "Attendance already marked for this date"}), 400

        # Insert the attendance data into the user-specific table
        cursor.execute(
            f"INSERT INTO {table_name} (rollNumber, name, father_name, mother_name, date_of_birth, class, category, gender, academicYear, attendance_month, time, date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (rollNumber, name, father_name, mother_name, date_of_birth, classValue, category, gender, academicYear, attendance_month, time, date)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Attendance marked successfully"})

    except psycopg2.Error as e:
        print("⚠️ PostgreSQL Error:", str(e))
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print("⚠️ Server error:", str(e))
        return jsonify({"error": "Server error: Could not mark attendance"}), 500

# Fetch Attendance Records API
@app.route('/attendance_records/<username>', methods=['GET'])
def get_attendance_records(username):
    try:
        conn = get_db_connection_att()
        if not conn:
            return jsonify({"error": "Database connection error"}), 500

        cursor = conn.cursor()
        table_name = f"attendance_{username}"

        # Check if the table exists
        cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
        if not cursor.fetchone()[0]:
            conn.close()
            return jsonify({"error": "Attendance table not found"}), 404

        # Fetch records from the table
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        conn.close()

        attendance_records = []
        for record in records:
            attendance_records.append({
                "rollNumber": record[1],
                "name": record[2],
                "father_name": record[3],
                "mother_name": record[4],
                "date_of_birth": record[5].strftime('%Y-%m-%d'),  # Format date as YYYY-MM-DD
                "class": record[6],
                "category": record[7],
                "gender": record[8],
                "academicYear": record[9],
                "attendance_month": record[10],
                "time": record[11],
                "date": record[12]
            })

        return jsonify({"records": attendance_records})

    except psycopg2.Error as e:
        print("⚠️ PostgreSQL Error:", str(e))
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print("⚠️ Server error:", str(e))
        return jsonify({"error": "Server error: Could not fetch attendance records"}), 500

# Start the Flask Server
if __name__ == '__main__':
    print(f"🚀 Starting server on port 5500...")
    app.run(host="0.0.0.0", port=5500, debug=False)
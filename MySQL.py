import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="master@123",
        database="biometeric_attendance"
    )
    print("✅ connected ''''Connected to MySQL!")
    conn.close()
except mysql.connector.Error as err:
    print("⚠️ MySQL Error:", err)
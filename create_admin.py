from werkzeug.security import generate_password_hash
from database import get_db_connection


username = "admin"
password = "admin123"

password_hash = generate_password_hash(password)


connection = get_db_connection()
cursor = connection.cursor()

cursor.execute(
    """
    INSERT INTO users (username, password_hash, role)
    VALUES (%s, %s, 'ADMIN')
    """,
    (username, password_hash)
)

connection.commit()

cursor.close()
connection.close()

print("Admin created successfully.")
print("Username:", username)
print("Password:", password)
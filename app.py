from flask import Flask
from database import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    return "Employee Cab Pooling System is running!"


@app.route("/test-db")
def test_db():
    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return f"Database connected successfully: {result[0]}"

    except Exception as error:
        return f"Database connection failed: {error}", 500


if __name__ == "__main__":
    app.run(debug=True)
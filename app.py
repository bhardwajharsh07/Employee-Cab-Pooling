from flask import Flask
from config import Config

from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.admin import admin_bp
from routes.booking import booking_bp


app = Flask(__name__)

app.config.from_object(Config)


# Register routes
app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp, url_prefix="/employee")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(booking_bp, url_prefix="/booking")


@app.route("/")
def home():
    return """
    <h1>Employee Cab Pooling System</h1>

    <p>
        <a href="/login">Login</a>
    </p>

    <p>
        <a href="/register">Register</a>
    </p>
    """


if __name__ == "__main__":
    app.run(debug=True)
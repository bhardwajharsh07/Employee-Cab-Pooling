from flask import Flask, render_template
from config import Config

from routes.auth import auth_bp
from routes.employee import employee_bp
from routes.admin import admin_bp
from routes.booking import booking_bp
from routes.pooling import pooling_bp


app = Flask(__name__)

app.config.from_object(Config)


# Register routes
app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp, url_prefix="/employee")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(booking_bp, url_prefix="/booking")
app.register_blueprint(pooling_bp, url_prefix="/pooling")


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
from flask import Flask
from models import init_db
from controllers.auth import auth_bp
from controllers.main import main_bp

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

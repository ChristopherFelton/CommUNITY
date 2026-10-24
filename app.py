from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
db = SQLAlchemy(app)
@app.route("/")
def home():
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return f"Database connected! Result: {result.scalar()}"
    except Exception as e:
        return f"Database connection failed: {e}", 500



if __name__ == "__main__":
    app.run(debug=True)

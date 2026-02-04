import os
from flask import Flask, render_template
from flask_migrate import Migrate
from database import db
from dotenv import load_dotenv
from flask_security.core import Security
from flask_security.datastore import SQLAlchemyUserDatastore
from seed import seedData, seed_security_staff
from services.statistics import Statistics
from Routes.customer_routes import customer_bp
from Routes.account_routes import account_bp
from Routes.admin_routes import admin_bp
from models.model import Employee, Role

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT")
app.config["SECURITY_PASSWORD_HASH"] = os.getenv("SECURITY_PASSWORD_HASH")
app.config["SECURITY_PASSWORD_SINGLE_HASH"] = False

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER"),
)
environment = os.getenv("FLASK_DEBUG") # Kolla upp!
db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(customer_bp)
app.register_blueprint(account_bp)
app.register_blueprint(admin_bp)

# Create a user datastore that registers users in our system
# Connects a user to a role
user_datastore = SQLAlchemyUserDatastore(db, Employee, Role)
Security(app, user_datastore)


@app.route("/")
def home():
    stats = Statistics(db.session).dashboard()
    return render_template("user/index.html", **stats) # index.html får med sig dict resultatet från .dashboard och kan då visa resultatet på sidan där.

# index.html har ingen direkt koppling till Python-funktioner.
# via render_template. Jinja ersätter sedan variablerna i HTML-filen
# Flask kör all logik i routen och skickar färdiga värden till templaten
# med dessa värden innan sidan skickas till klienten.

@app.route("/country/<string:country_code>")
def country_details(country_code: str):
    stats_service = Statistics(db.session)

    top_customers = stats_service.top_customers_by_country(country_code, limit=10)

    return render_template(
        "/country.html",
        country_code=country_code,
        top_customers=top_customers
    )


if __name__ == "__main__":

    if os.environ.get("FLASK_DEBUG") == "1": # Kolla upp!
        with app.app_context():
            # We need the app_context when using the db outside of a request
            seedData(db)
            seed_security_staff(db, user_datastore)
    
        app.run(debug=True)
    else:
        app.run()

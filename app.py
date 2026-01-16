import os
from flask import Flask, render_template
from flask_migrate import Migrate
from livereload import Server
from database import db
from dotenv import load_dotenv
from seed import seedData
from services.statistics import Statistics
from Routes.customer_routes import customer_bp

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
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


@app.route("/")
def home():
    stats = Statistics(db.session).dashboard()
    return render_template("user/index.html", **stats) # index.html får med sig dict resultatet från .dashboard och kan då visa resultatet på sidan där.

# index.html har ingen direkt koppling till Python-funktioner.
# via render_template. Jinja ersätter sedan variablerna i HTML-filen
# Flask kör all logik i routen och skickar färdiga värden till templaten
# med dessa värden innan sidan skickas till klienten.


if __name__ == "__main__":

    if os.environ.get("FLASK_DEBUG") == "1": # Kolla upp!
        with app.app_context():
            # We need the app_context when using the db outside of a request
            seedData(db)
        server = Server(app.wsgi_app)
        server.watch("templates/**/*.html")  # all HTML files recursively
        server.watch("templates/components/*.html")  # or specific subfolder
        server.watch("static/**/*.css")       # watch CSS recursively
        server.watch("static/**/*.js")        # watch JS

        server.serve(open_url_delay=True)
    else:
        app.run()

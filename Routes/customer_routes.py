from flask import Blueprint, render_template
from database import db
from models.model import Customer

customer_bp = Blueprint('customer', __name__, url_prefix='/customer') # 'customer' efter Blueprint är namnet som länken i navbar letar efter.

@customer_bp.route("/")
def get_all():
    customers: list[Customer] = db.session.query(Customer).all()
    return render_template("user/customer/customers.html")



@customer_bp.route("/<int:id>")
def get_one():
    customer: Customer | None = db.session.get(Customer, id)
    return render_template("user/customer/customer.html")
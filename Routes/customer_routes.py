from flask import Blueprint, render_template, abort, request
from services.customer_service import CustomerService

customer_bp = Blueprint('customer', __name__, url_prefix='/customer') # 'customer' efter Blueprint är namnet som länken i navbar letar efter.

@customer_bp.route("/")
def get_all():

    q = request.args.get("q", default= "", type=str).strip()
    city = request.args.get("city", default="", type=str).strip()

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=50, type=int)

    sort_by = request.args.get("sort_by", default="Id", type=str)
    sort_order = request.args.get("sort_order", default="asc", type=str)

    pagination = CustomerService.get_paginated(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        city=city
    )

    return render_template(
        "user/customer/customers.html",
        pagination=pagination,
        customers=pagination.items,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        city=city
    )



@customer_bp.route("/<int:id>")
def get_one(id: int):
    customer= CustomerService.get_by_id(id)

    if not customer:
        abort(404)

    return render_template("user/customer/customer.html", customer = customer)
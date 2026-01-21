from flask import Blueprint, render_template, abort, request, redirect, url_for
from services.customer_service import CustomerService
from decimal import Decimal
from typing import cast
from models.model import Account

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

    accounts = cast(list[Account], customer.Accounts)
    total_balance = sum(acc.Balance for acc in accounts)

    return render_template("user/customer/customer.html", customer = customer, total_balance=total_balance)


@customer_bp.route("/by_id")
def by_id():
    customer_id = request.args.get("id", type=int)

    if not customer_id:
        abort(400)

    customer = CustomerService.get_by_id(customer_id)

    if not customer:
        abort(404)

    return redirect(url_for("customer.get_one", id=customer.Id))
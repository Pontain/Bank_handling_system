from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from services.customer_service import CustomerService
from decimal import Decimal
from typing import cast
from database import db
from models.model import Account, Customer
from forms.forms import CustomerCreateForm
from utils.form_mappers import prefill_customer_form, apply_customer_form

customer_bp = Blueprint('customer', __name__, url_prefix='/customer') # 'customer' efter Blueprint är namnet som länken i navbar letar efter.

@customer_bp.route("/")
def get_all():

    q = request.args.get("q", default= "", type=str).strip() # fritext-sökning
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
        abort(404) # returnerar 404, not found, fel utan krasch

    accounts = cast(list[Account], customer.Accounts) # cast hjälper type checkers, inte runtime
    total_balance = sum(acc.Balance for acc in accounts)

    return render_template("user/customer/customer.html", customer = customer, total_balance=total_balance)


@customer_bp.route("/by_id")
def by_id():
    customer_id = request.args.get("id", type=int)

    if not customer_id:
        abort(400) # klienten skickade nått fel.

    customer = CustomerService.get_by_id(customer_id)

    if not customer:
        abort(404)

    return redirect(url_for("customer.get_one", id=customer.Id)) # /customer/by_id?id=5 → redirect → /customer/5


@customer_bp.route("/create", methods=["GET", "POST"])
def create_customer():
    form = CustomerCreateForm()

    if form.validate_on_submit():
        customer = Customer()
        apply_customer_form(customer, form)

        db.session.add(customer)
        db.session.commit()

        flash("Customer created", "success")
        return redirect(url_for("customer.get_all"))

    if request.method == "POST" and not form.validate_on_submit():
        flash(f"Form errors: {form.errors}", "danger")


    return render_template("user/customer/create_customer.html", form=form)


@customer_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_customer(id: int):
    customer = CustomerService.get_by_id(id)

    if not customer or customer.is_deleted:
        abort(404)

    form = CustomerCreateForm()

    if request.method == "GET":
        prefill_customer_form(form, customer)

    if form.validate_on_submit():
        apply_customer_form(customer, form)
        db.session.commit()
        flash("Customer updated", "success")
        return redirect(url_for("customer.get_one", id=customer.Id))

    if request.method == "POST" and not form.validate_on_submit():
        flash(f"Form errors: {form.errors}", "danger")



    return render_template(
        "user/customer/edit_customer.html",
        form=form,
        customer=customer,
    )

@customer_bp.post("/<int:id>/delete")
def delete_customer(id: int):
    customer = CustomerService.get_by_id(id)

    if not customer:
        abort(404)

    customer.soft_delete()
    db.session.commit()

    flash("Customer deleted", "success")
    return redirect(url_for("customer.get_all"))

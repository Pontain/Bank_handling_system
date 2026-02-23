from __future__ import annotations

from flask import Blueprint, jsonify
from flask_security.decorators import auth_required, roles_required

from services.customer_service import CustomerService

customers_api = Blueprint("api", __name__, url_prefix="/api")


@customers_api.get("/<int:customer_id>")
@auth_required()
@roles_required("CASHIER")
def get_customer(customer_id: int):
    customer = CustomerService.get_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    return jsonify({
        "Id": customer.Id,
        "GivenName": customer.GivenName,
        "Surname": customer.Surname,
        "NationalId": customer.NationalId,
        "Streetaddress": customer.Streetaddress,
        "City": customer.City,
        "Zipcode": customer.Zipcode,
        "Country": customer.Country,
        "EmailAddress": customer.EmailAddress,
        "Telephone": customer.Telephone,
    })
from typing import Any
from database import db
from models.model import Customer
from sqlalchemy import select, or_

class CustomerService:

    SORT_COLUMNS: dict[str, Any] = {
        "Id": Customer.Id,
        "GivenName": Customer.GivenName,
        "Surname": Customer.Surname,
        "City": Customer.City,
        "NationalId": Customer.NationalId,
    }

    @staticmethod
    def get_paginated(page: int, per_page: int, sort_by: str, sort_order: str, q: str = "", city: str = ""):
        sort_col = CustomerService.SORT_COLUMNS.get(sort_by, Customer.Id)

        stmt = select(Customer)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Customer.GivenName.ilike(like),
                    Customer.Surname.ilike(like),
                )
            )

        if city:
            stmt = stmt.where(Customer.City.ilike(f"%{city}%"))

        if sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        return db.paginate(
            stmt,
            page=page,
            per_page=per_page,
            error_out=False
        )

    @staticmethod
    def get_by_id(customer_id: int) -> Customer | None:
        return db.session.get(Customer, customer_id)

    # @staticmethod
    # def search(name: str, ):
        
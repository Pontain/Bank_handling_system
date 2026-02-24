from typing import Any
from database import db
from models.model import Customer, Account, AccountType
from sqlalchemy import select, or_

class CustomerService:

    SORT_COLUMNS: dict[str, Any] = { # Detta är en whitelist (tillåten lista) över vilka kolumner man får sortera på. Any är här för att typa SQL-attribut.
        "Id": Customer.Id,
        "GivenName": Customer.GivenName,
        "Surname": Customer.Surname,
        "City": Customer.City,
        "NationalId": Customer.NationalId,
        "Streetaddress": Customer.Streetaddress
    }

    @staticmethod
    def create_with_default_account(customer: Customer) -> Customer:
        """
        Skapar en kund och ett defaultkonto i samma transaktion.
        """
        try:
            db.session.add(customer)
            db.session.flush()  # ger customer.Id utan commit

            default_account = Account(
                CustomerId=customer.Id,
                AccountType=AccountType.PERSONAL,
                Balance=0
            )
            db.session.add(default_account)

            db.session.commit()
            return customer
        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def get_paginated(page: int, per_page: int, sort_by: str, sort_order: str, q: str = "", city: str = ""):
       
        sort_col = CustomerService.SORT_COLUMNS.get(sort_by, Customer.Id) # Om sort_by är något okänt → fallback till Customer.Id

        stmt = select(Customer).where(Customer.is_deleted.is_(False)) # SELECT * FROM customer

        if q:
            like = f"%{q}%" # %% betyder matcha vadsomhelst före och efter
            stmt = stmt.where(
                or_(
                    Customer.GivenName.ilike(like), # .ilike = case insensitive
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
            error_out=False # ger en tom lista ifall klienten skriver fel.
        )

    @staticmethod
    def get_by_id(customer_id: int) -> Customer | None:
        return db.session.get(Customer, customer_id)

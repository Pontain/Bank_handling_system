from enum import Enum as PyEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, text, Numeric
from decimal import Decimal
from typing import Annotated
from database import db



class Types:
    int_pk = Annotated[
        int, mapped_column(Integer, primary_key=True, autoincrement=True)
    ]


class Customer(db.Model):
    __tablename__ = "customers"
    Id: Mapped[Types.int_pk]
    GivenName = mapped_column(db.String(50), unique=False, nullable=False)
    Surname = mapped_column(db.String(50), unique=False, nullable=False)
    Streetaddress = mapped_column(db.String(50), unique=False, nullable=False)
    City = mapped_column(db.String(50), unique=False, nullable=False)
    Zipcode = mapped_column(db.String(10), unique=False, nullable=False)
    Country = mapped_column(db.String(30), unique=False, nullable=False)
    CountryCode = mapped_column(db.String(2), unique=False, nullable=False)
    Birthday = mapped_column(db.DateTime, unique=False, nullable=False)
    NationalId = mapped_column(db.String(20), unique=False, nullable=False)
    TelephoneCountryCode = mapped_column(db.Integer, unique=False, nullable=False)
    Telephone = mapped_column(db.String(20), unique=False, nullable=False)
    EmailAddress = mapped_column(db.String(50), unique=False, nullable=False)

    Accounts = db.relationship("Account", backref="customer", lazy=True)


class AccountType(PyEnum):
    PERSONAL = "PERSONAL"
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class Account(db.Model):
    __tablename__ = "accounts"
    Id: Mapped[Types.int_pk]
    AccountType = mapped_column(
        db.Enum(AccountType),
        default=AccountType.PERSONAL,
        server_default=text(f"'{AccountType.PERSONAL.value}'"),
        unique=False,
        nullable=False,
    )
    Created = mapped_column(db.DateTime, unique=False, nullable=False)
    Balance = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    Transactions = db.relationship("Transaction", backref="account", lazy=True)
    CustomerId = mapped_column(
        db.Integer, db.ForeignKey("customers.Id"), nullable=False
    )


class Transaction(db.Model):
    __tablename__ = "transactions"
    Id: Mapped[Types.int_pk]
    Type = mapped_column(db.String(20), unique=False, nullable=False)
    Operation = mapped_column(db.String(50), unique=False, nullable=False)
    Date = mapped_column(db.DateTime, unique=False, nullable=False)
    Amount = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    NewBalance = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    AccountId = mapped_column(db.Integer, db.ForeignKey("accounts.Id"), nullable=False)



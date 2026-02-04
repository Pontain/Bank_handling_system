
# pyright: reportIncompatibleVariableOverride=false
import uuid
from datetime import date
from enum import Enum as PyEnum
from flask_sqlalchemy.table import _Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, UniqueConstraint, text, Numeric
from decimal import Decimal
from typing import Annotated
from database import db
from models.mixin import SoftDeletionMixin, TimestampMixin
from flask_security.core import UserMixin, RoleMixin


class Types:
    int_pk = Annotated[
        int, mapped_column(Integer, primary_key=True, autoincrement=True)
    ]


class Customer(TimestampMixin, SoftDeletionMixin, db.Model):
    __tablename__ = "customers"
    Id: Mapped[Types.int_pk]
    GivenName: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    Surname: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    Streetaddress: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    City: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    Zipcode: Mapped[str] = mapped_column(db.String(10), unique=False, nullable=False)
    Country: Mapped[str] = mapped_column(db.String(30), unique=False, nullable=False)
    CountryCode: Mapped[str] = mapped_column(db.String(2), unique=False, nullable=False)
    Birthday: Mapped[date | None] = mapped_column(db.Date, unique=False, nullable=False)
    NationalId: Mapped[str] = mapped_column(db.String(20), unique=False, nullable=False)
    Telephone: Mapped[str] = mapped_column(db.String(20), unique=False, nullable=False)
    EmailAddress: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)

    Accounts = db.relationship("Account", backref="customer", lazy=True)


class AccountType(PyEnum):
    PERSONAL = "PERSONAL"
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class Account(TimestampMixin, db.Model):
    __tablename__ = "accounts"
    Id: Mapped[Types.int_pk]
    AccountType = mapped_column(
        db.Enum(AccountType),
        default=AccountType.PERSONAL,
        server_default=text(f"'{AccountType.PERSONAL.value}'"),
        unique=False,
        nullable=False,
    )
    Balance = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    Transactions = db.relationship("Transaction", backref="account", lazy=True)
    CustomerId = mapped_column(
        db.Integer, db.ForeignKey("customers.Id"), nullable=False
    )


class Transaction(TimestampMixin, db.Model):
    __tablename__ = "transactions"
    Id: Mapped[Types.int_pk]
    Type = mapped_column(db.String(20), unique=False, nullable=False)
    Operation = mapped_column(db.String(50), unique=False, nullable=False)
    Date = mapped_column(db.DateTime, unique=False, nullable=False)
    Amount = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    NewBalance = mapped_column(Numeric(18, 2), unique=False, nullable=False)
    AccountId = mapped_column(db.Integer, db.ForeignKey("accounts.Id"), nullable=False)


# Ej en klass här då tabellen inte innehåller data, enbart för att koppla Empoyee med role.
roles_employees: _Table = db.Table(
    "roles_employees",
    db.Column("employee_id", db.Integer, db.ForeignKey("employees.id")),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id")),
)

class Role(db.Model, RoleMixin):
    __tablename__ = "roles"
    id: Mapped[Types.int_pk]
    name: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(db.String(100), nullable=True)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        secondary=roles_employees,
        back_populates="roles",
        lazy="selectin",
    )


class Employee(db.Model, UserMixin, SoftDeletionMixin):
    __tablename__ = "employees"
    id: Mapped[Types.int_pk]

    # Flask-Security brukar använda email som login-id
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)

    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    active: Mapped[bool] = mapped_column(db.Boolean, default=True, server_default=text("1"))

    # Viktig för nyare Flask-Security
    fs_uniquifier: Mapped[str] = mapped_column(
        db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex
    )

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=roles_employees,
        back_populates="employees",
        lazy="selectin",
    )
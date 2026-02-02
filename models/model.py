from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, UniqueConstraint, text, Numeric
from decimal import Decimal
from typing import Annotated
from database import db
from models.mixin import SoftDeletionMixin, TimestampMixin


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
    Birthday: Mapped[datetime] = mapped_column(db.DateTime, unique=False, nullable=False)
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


class StaffRole(PyEnum): # Enum, pyenum innebär att detta fält får bara innehålla något från den listan.
    CASHIER = "CASHIER"
    ADMIN = "ADMIN"


class StaffUser(TimestampMixin, SoftDeletionMixin, db.Model):
    __tablename__ = "staff_users"

    Id: Mapped[Types.int_pk]

    Username: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    PasswordHash: Mapped[str | None] = mapped_column(db.String(255), nullable=True) #hashat password för login.

    IsActive: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    # Kopplingar (roller)
    Roles = relationship(
        "StaffUserRole",
        back_populates="User",
        cascade="all, delete-orphan",
        lazy="selectin", # fixar en lista med objekt istället för en query per objekt.
    )

    # Helper-metoder (bra för route-guards)
    def has_role(self, role: StaffRole | str) -> bool:
        role_value = role.value if isinstance(role, StaffRole) else str(role)
        return any(ur.Role.value == role_value for ur in self.Roles)

    def add_role(self, role: StaffRole) -> None:
        if not self.has_role(role):
            self.Roles.append(StaffUserRole(Role=role))

    def remove_role(self, role: StaffRole) -> None:
        self.Roles = [ur for ur in self.Roles if ur.Role != role]


class StaffUserRole(db.Model):

    # Association table i ORM-form (enum-kolumn + unik constraint)

    __tablename__ = "staff_user_roles"
    __table_args__ = (
        UniqueConstraint("StaffUserId", "Role", name="uq_staff_user_role"),
    )

    Id: Mapped[Types.int_pk]

    StaffUserId: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("staff_users.Id"), nullable=False
    )

    Role: Mapped[StaffRole] = mapped_column(
        db.Enum(StaffRole),
        nullable=False,
    )

    User = relationship("StaffUser", back_populates="Roles")
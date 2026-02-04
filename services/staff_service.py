from __future__ import annotations

from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from database import db
from models.model import Employee, Role

from flask_security.utils import hash_password


class StaffService:
    """
    Service för personal (employees) baserat på Flask-Security modeller.

    Admin kan:
      - lista personal (paginering/sök/sort)
      - skapa personal (med hashat lösenord)
      - aktivera/inaktivera (active)
      - sätta / ta bort roller (many-to-many via roles)
    """

    SORT_COLUMNS: dict[str, Any] = {
        "id": Employee.id,
        "email": Employee.email,
        "username": Employee.username,
        "active": Employee.active,
    }

    # ----------------------------
    # CREATE
    # ----------------------------
    @staticmethod
    def create_user(
        email: str,
        username: str,
        password_plain: str,
        role_names: list[str] | None = None,
        active: bool = True,
    ) -> Employee:
        """
        Skapar en Employee med hashat lösenord och valfria roller.
        role_names är t.ex. ["ADMIN", "CASHIER"].
        """
        try:
            user = Employee(
                email=email.lower().strip(),
                username=username.strip(),
                password=hash_password(password_plain),
                active=active,
            )

            if role_names:
                roles = StaffService.get_roles_by_names(role_names)
                user.roles = roles

            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    # ----------------------------
    # READ
    # ----------------------------
    @staticmethod
    def get_by_id(employee_id: int) -> Employee | None:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.roles))
            .where(Employee.id == employee_id)
        )
        return db.session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_email(email: str) -> Employee | None:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.roles))
            .where(Employee.email == email.lower().strip())
        )
        return db.session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_username(username: str) -> Employee | None:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.roles))
            .where(Employee.username == username.strip())
        )
        return db.session.execute(stmt).scalars().first()

    @staticmethod
    def get_roles_by_names(role_names: list[str]) -> list[Role]:
        """
        Hämtar Role-objekt för givna rollnamn. Ignorerar namn som inte finns.
        """
        clean = [r.strip().upper() for r in role_names if r and r.strip()]
        if not clean:
            return []

        stmt = select(Role).where(Role.name.in_(clean))
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def get_paginated(
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        q: str = "",
        include_inactive: bool = False,
    ):
        """
        Hämtar personal paginerat.
        - q söker i email/username
        - include_inactive: om False visar vi bara active=True
        """
        sort_col = StaffService.SORT_COLUMNS.get(sort_by, Employee.id)

        stmt = (
            select(Employee)
            .where(Employee.is_deleted.is_(False))
            .options(selectinload(Employee.roles))
        )

        if not include_inactive:
            stmt = stmt.where(Employee.active.is_(True))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Employee.email.ilike(like),
                    Employee.username.ilike(like),
                )
            )

        stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    # ----------------------------
    # UPDATE
    # ----------------------------
    @staticmethod
    def set_active(employee_id: int, is_active: bool) -> None:
        try:
            user = db.session.get(Employee, employee_id)
            if not user:
                return
            user.active = is_active
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_roles(employee_id: int, role_names: list[str]) -> None:
        """
        Ersätter alla roller för en user med nya roller baserat på namn.
        """
        try:
            user = db.session.get(Employee, employee_id)
            if not user:
                return

            roles = StaffService.get_roles_by_names(role_names)
            user.roles = roles

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def add_role(employee_id: int, role_name: str) -> None:
        try:
            user = db.session.get(Employee, employee_id)
            if not user:
                return

            role = db.session.execute(
                select(Role).where(Role.name == role_name.strip().upper())
            ).scalars().first()

            if not role:
                return

            if role not in user.roles:
                user.roles.append(role)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def remove_role(employee_id: int, role_name: str) -> None:
        try:
            user = db.session.get(Employee, employee_id)
            if not user:
                return

            target = role_name.strip().upper()
            user.roles = [r for r in user.roles if r.name != target]

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id_including_deleted(id: int):
        stmt = (
            select(Employee)
            .where(Employee.id == id)
            .options(selectinload(Employee.roles))
        )
        return db.session.scalar(stmt)

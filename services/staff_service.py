from __future__ import annotations # även bra för att import-ordningen inte spelar någon roll

from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from database import db
from models.model import StaffUser, StaffRole


class StaffService:

    # Service för personal (staff_users).
    # Admin kommer kunna:
    #   - lista personal
    #   - skapa personal
    #   - inaktivera (soft delete / is_active)
    #   - sätta / ta bort roller


    SORT_COLUMNS: dict[str, Any] = {
        "Id": StaffUser.Id,
        "Username": StaffUser.Username,
        "IsActive": StaffUser.IsActive,
    }


    @staticmethod
    def create_user(username: str, roles: list[StaffRole] | None = None) -> StaffUser:

        # Skapar en personal-användare.
        # Lösenord sätts senare.

        try:
            user = StaffUser(
                Username=username,
                PasswordHash=None,
                IsActive=True,
            )

            # Lägg roller direkt (valfritt)
            if roles:
                for role in roles:
                    user.add_role(role)

            db.session.add(user)
            db.session.commit()
            return user

        except Exception:
            db.session.rollback()
            raise

    # Lista all personal

    @staticmethod
    def get_paginated(
        page: int,
        per_page: int,
        sort_by: str,
        sort_order: str,
        q: str = "",
        include_inactive: bool = False,
    ):

        # Hämtar personal paginerat.
        # - q söker i username
        # - include_inactive: om False visar vi bara IsActive=True

        sort_col = StaffService.SORT_COLUMNS.get(sort_by, StaffUser.Id)

        stmt = select(StaffUser).options(
            # gör att user.Roles redan finns redo utan N+1
            selectinload(StaffUser.Roles)
        )

        # soft delete-filter (om din SoftDeletionMixin har is_deleted)
        # Anpassa om din mixin heter något annat.
        stmt = stmt.where(StaffUser.is_deleted.is_(False))

        if not include_inactive:
            stmt = stmt.where(StaffUser.IsActive.is_(True))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    StaffUser.Username.ilike(like),
                )
            )

        stmt = stmt.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    # Hämta en user med id och sen med namn.
    @staticmethod
    def get_by_id(staff_user_id: int) -> StaffUser | None:

        # Hämtar en user + roller.
        # Här använder vi select för en och samma user, och laddar rollerna.

        stmt = (
            select(StaffUser)
            .options(selectinload(StaffUser.Roles))
            .where(StaffUser.Id == staff_user_id)
            .where(StaffUser.is_deleted.is_(False))
        )
        return db.session.execute(stmt).scalars().first()

    @staticmethod
    def get_by_username(username: str) -> StaffUser | None:
        stmt = (
            select(StaffUser)
            .options(selectinload(StaffUser.Roles))
            .where(StaffUser.Username == username)
            .where(StaffUser.is_deleted.is_(False))
        )
        return db.session.execute(stmt).scalars().first()

    # Aktivera en user
    @staticmethod
    def set_active(staff_user_id: int, is_active: bool) -> None:
        try:
            user = db.session.get(StaffUser, staff_user_id)
            if not user or user.is_deleted:
                return

            user.IsActive = is_active
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


    @staticmethod
    def add_role(staff_user_id: int, role: StaffRole) -> None:

        # Lägger till en roll till user.
        # Unik constraint + has_role() skyddar mot dubletter.

        try:
            user = StaffService.get_by_id(staff_user_id)
            if not user:
                return

            user.add_role(role)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def remove_role(staff_user_id: int, role: StaffRole) -> None:
        try:
            user = StaffService.get_by_id(staff_user_id)
            if not user:
                return

            user.remove_role(role)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_roles(staff_user_id: int, roles: list[StaffRole]) -> None:
      
        try:
            user = StaffService.get_by_id(staff_user_id)
            if not user:
                return

            # ta bort allt
            user.Roles = []

            # lägg till nya
            for r in roles:
                user.add_role(r)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    # ----------------------------
    # DELETE (soft delete)
    # ----------------------------
    @staticmethod
    def soft_delete(staff_user_id: int) -> None:

        try:
            user = db.session.get(StaffUser, staff_user_id)
            if not user:
                return

            user.is_deleted = True

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

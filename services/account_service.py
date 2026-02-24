from database import db
from models.model import Account, Transaction
from sqlalchemy import select


class AccountService:

    @staticmethod
    def get_by_id(account_id: int) -> Account | None:
        return db.session.get(Account, account_id)
    
    @staticmethod
    def get_transactions(account_id: int, limit: int = 50, offset: int = 0) -> list[Transaction]:

        stmt= ( # stmt = statement -> standardkonvention i SQL alchemy
            select(Transaction)
            .where(Transaction.AccountId == account_id)
            .order_by(Transaction.Date.desc(), Transaction.Id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.session.scalars(stmt).all())
    
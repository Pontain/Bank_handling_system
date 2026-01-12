from sqlalchemy import func
from models.model import Customer, Account, Transaction

class Statistics:
    def __init__(self, session):
        self.session= session

    def customer_count(self) -> int:
        return self.session.query(func.count(Customer.Id)).scalar() or 0 # scalar skalar ner resultatet till enbart värdet uran paranteser osv.
    
    def account_count(self) -> int:
        return self.session.query(func.count(Account.Id)).scalar() or 0
    
    def total_per_account(self):
        return (
            self.session.query(
                Account.Id,
                func.coalesce(func.sum(Transaction.Amount), 0).label("Total")
            )
            .outerjoin(Transaction, Transaction.Id == Account.Id)
            .group_by(Account.Id)
            .order_by(Account.Id)
            .all()
        )

    def dashboard(self) -> dict:
        return {"customer_count": self.customer_count(),
                "account_count": self.account_count(),
                "totals_per_account": self.total_per_account()
                }

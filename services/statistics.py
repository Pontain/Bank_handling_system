from sqlalchemy import Row, func
from models.model import Customer, Account, Transaction

class Statistics:
    def __init__(self, session):
        self.session= session

    def customer_count(self) -> int:
        return self.session.query(func.count(Customer.Id)).scalar() or 0 # scalar skalar ner resultatet till enbart värdet uran paranteser osv.
    
    def account_count(self) -> int:
        return self.session.query(func.count(Account.Id)).scalar() or 0
    
    def total_per_account(self) -> list[Row]:

        total_expr = func.coalesce(func.sum(Transaction.Amount), 0)  # coalesence betyder "fuse" och omvanlar NULL, alltså inga transaktioner, till 0.

        return (
            self.session.query(
                Account.Id,
                total_expr.label("total")
            )
            .outerjoin(Transaction, Transaction.AccountId == Account.Id) # Med outerjoin får vi även med konton som inte har några transaktioner.
            .group_by(Account.Id)
            .order_by(total_expr.desc())
            .limit(10)
            .all()
        )
    
    def total_balance_all_accounts(self):
        return (
            self.session.query(func.coalesce(func.sum(Transaction.Amount), 0))
            .scalar()
            or 0
        )

    def dashboard(self) -> dict: # Packar ner allt i en låda typ. De tre funktionerna körs och läggs i en dict. Detta kan sen köras via rout till en template.
        return {"customer_count": self.customer_count(),
                "account_count": self.account_count(),
                "totals_per_account": self.total_per_account(),
                "total_balance_all_accounts": self.total_balance_all_accounts()
                }

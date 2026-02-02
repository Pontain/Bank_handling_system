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
    
    def available_countries(self) -> list[str]:
        return [
            row[0]
            for row in self.session.query(Customer.CountryCode)
            .distinct()
            .order_by(Customer.CountryCode)
            .all()
        ]


    def summary_per_country(self) -> list[Row]:
        country_col = Customer.CountryCode

        total_expr = func.coalesce(func.sum(Transaction.Amount), 0)

        return (
            self.session.query(
                country_col.label("country"),
                func.count(func.distinct(Customer.Id)).label("customer_count"),
                func.count(func.distinct(Account.Id)).label("account_count"),
                total_expr.label("total_balance")
            )
            .join(Account, Account.CustomerId == Customer.Id)
            .outerjoin(Transaction, Transaction.AccountId == Account.Id)
            .group_by(country_col)
            .order_by(total_expr.desc())
            .all()
        )

    def top_customers_by_country(self, country_code: str, limit: int = 10) -> list[Row]:
        country_col = Customer.CountryCode
        total_expr = func.coalesce(func.sum(Transaction.Amount), 0)

        return (
            self.session.query(
                Customer.Id.label("customer_id"),
                Customer.GivenName.label("given_name"),
                Customer.Surname.label("surname"),
                total_expr.label("total_balance")
            )
            .join(Account, Account.CustomerId == Customer.Id)
            .outerjoin(Transaction, Transaction.AccountId == Account.Id)
            .filter(country_col == country_code)
            .group_by(Customer.Id, Customer.GivenName, Customer.Surname)
            .order_by(total_expr.desc(), Customer.Id.asc())
            .limit(limit)
            .all()
        )


    def dashboard(self) -> dict: # Packar ner allt i en låda typ. De tre funktionerna körs och läggs i en dict. Detta kan sen köras via rout till en template.
        return {"customer_count": self.customer_count(),
                "account_count": self.account_count(),
                "totals_per_account": self.total_per_account(),
                "total_balance_all_accounts": self.total_balance_all_accounts(),
                "countries": self.available_countries()
                }

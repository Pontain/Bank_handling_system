from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from database import db
from models.model import Account, Transaction


# -----------------------------
# Exceptions
# -----------------------------

@dataclass
class InsufficientFundsError(Exception):
    account_id: int
    balance: Decimal
    requested: Decimal

    def __str__(self) -> str:
        return (
            f"Otillräckligt saldo på konto {self.account_id}. "
            f"Saldo: {self.balance:.2f}, försök: {self.requested:.2f}"
        )


class InvalidAmountError(Exception):
    pass


# -----------------------------
# Money helpers
# -----------------------------

TWOPLACES = Decimal("0.01")


def _to_money(value: Decimal | int | str | float) -> Decimal:
    """
    Konverterar säkert till Decimal:
    - stoppar flyttalsbrus (via str)
    - tvingar 2 decimaler (ROUND_HALF_UP)
    """
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    return d.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


# -----------------------------
# Pure logic result type (unit-test friendly)
# -----------------------------

@dataclass(frozen=True)
class TxResult:
    NewBalance: Decimal


# -----------------------------
# Service
# -----------------------------

class TransactionService:
    """
    Enda stället i koden som ska få uppdatera Account.Balance (för DB-flöden).
    Routes/användare ska aldrig röra Balance direkt.
    """

    # -------- DB helpers --------

    @staticmethod
    def _lock_account(session: Session | scoped_session[Session], account_id: int) -> Account:
        """
        SELECT ... FOR UPDATE för att undvika race conditions.
        (Notera: bäst stöd i MySQL/Postgres; SQLite kan bete sig annorlunda.)
        """
        stmt = (
            select(Account)
            .where(Account.Id == account_id)
            .with_for_update()
        )
        account = session.scalars(stmt).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")
        return account

    # -------- Pure logic (no DB) --------
    # Dessa används i unit tests, och kan även återanvändas i DB-metoderna.

    @staticmethod
    def deposit_logic(account: Account, amount) -> TxResult:
        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        new_balance = _to_money(account.Balance) + amt
        account.Balance = new_balance
        return TxResult(NewBalance=new_balance)

    @staticmethod
    def withdraw_logic(account: Account, amount) -> TxResult:
        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        balance = _to_money(account.Balance)
        if amt > balance:
            raise InsufficientFundsError(account.Id, balance, amt)

        new_balance = balance - amt
        account.Balance = new_balance
        return TxResult(NewBalance=new_balance)

    @staticmethod
    def transfer_logic(from_account: Account, to_account: Account, amount) -> tuple[TxResult, TxResult]:
        w = TransactionService.withdraw_logic(from_account, amount)
        d = TransactionService.deposit_logic(to_account, amount)
        return w, d

    # -------- DB methods (integration) --------

    @staticmethod
    def deposit(account_id: int, amount, operation: str = "Deposit") -> Transaction:
        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        session = db.session
        account = TransactionService._lock_account(session, account_id)

        # använd samma logik som unit-testas
        res = TransactionService.deposit_logic(account, amt)

        tx = Transaction(
            Type="CREDIT",
            Operation=operation,
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=res.NewBalance,
            AccountId=account.Id,
        )

        session.add(tx)
        session.commit()
        return tx

    @staticmethod
    def withdraw(account_id: int, amount, operation: str = "Withdraw") -> Transaction:
        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        session = db.session
        account = TransactionService._lock_account(session, account_id)

        # använd samma logik som unit-testas
        res = TransactionService.withdraw_logic(account, amt)

        tx = Transaction(
            Type="DEBIT",
            Operation=operation,
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=res.NewBalance,
            AccountId=account.Id,
        )

        session.add(tx)
        session.commit()
        return tx

    @staticmethod
    def transfer(from_account_id: int, to_account_id: int, amount) -> tuple[Transaction, Transaction]:
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")

        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        session = db.session

        # Lås i stabil ordning för att minska deadlocks
        first_id, second_id = sorted([from_account_id, to_account_id])
        first = TransactionService._lock_account(session, first_id)
        second = TransactionService._lock_account(session, second_id)

        from_acc = first if first.Id == from_account_id else second
        to_acc = second if from_acc is first else first

        # använd samma logik som unit-testas
        res_out, res_in = TransactionService.transfer_logic(from_acc, to_acc, amt)

        tx_out = Transaction(
            Type="DEBIT",
            Operation=f"Transfer to account nr: {to_acc.Id}",
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=res_out.NewBalance,
            AccountId=from_acc.Id,
        )

        tx_in = Transaction(
            Type="CREDIT",
            Operation=f"Transfer from account nr: {from_acc.Id}",
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=res_in.NewBalance,
            AccountId=to_acc.Id,
        )

        session.add_all([tx_out, tx_in])
        session.commit()

        return tx_out, tx_in
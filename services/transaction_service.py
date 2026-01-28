from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import db
from models.model import Account, Transaction


# Tydliga feltyper (lätta att fånga i routes och visa flash-meddelande)

@dataclass
class InsufficientFundsError(Exception): # Exception fångar alla fel som ärver från python inbyggda exception.
    account_id: int
    balance: Decimal
    requested: Decimal

    def __str__(self) -> str: # __str__ är som __repr__ men mer anpassat för användare.
        return (
            f"Otillräckligt saldo på konto {self.account_id}. "
            f"Saldo: {self.balance:.2f}, försök: {self.requested:.2f}"
        )


class InvalidAmountError(Exception):
    pass


# ---- Service ----

TWOPLACES = Decimal("0.01") # Minsta valutaenhet.


def _to_money(value: Decimal | int | str | float) -> Decimal:
    
    # Konverterar säkert till Decimal, Stoppar flyttalsbrus, Säkerställer exakt två decimaler innan DB och affärslogik

    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    return d.quantize(TWOPLACES, rounding=ROUND_HALF_UP) # Decimal.quantize() används för att tvinga ett Decimal-tal till ett bestämt antal decimaler, med kontrollerad avrundning.


class TransactionService:
    """
    Enda stället i koden som ska få uppdatera Account.Balance.
    Routes/användare ska aldrig röra Balance direkt.
    """

    @staticmethod
    def _lock_account(session: Session, account_id: int) -> Account:
        """
        SELECT ... FOR UPDATE för att undvika att två uttag samtidigt
        kan gå igenom på samma saldo.
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

    @staticmethod
    def deposit(account_id: int, amount, operation: str = "Deposit") -> Transaction:
        amt = _to_money(amount)
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        session = db.session
        account = TransactionService._lock_account(session, account_id)

        new_balance = _to_money(account.Balance) + amt

        tx = Transaction(
            Type="CREDIT",
            Operation=operation,
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=new_balance,
            AccountId=account.Id,
        )

        # Uppdatera saldo endast här, som en bieffekt av transaktionen
        account.Balance = new_balance

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

        current = _to_money(account.Balance)
        if current < amt:
            raise InsufficientFundsError(account.Id, current, amt)

        new_balance = current - amt

        tx = Transaction(
            Type="DEBIT",
            Operation=operation,
            Date=datetime.utcnow(),
            Amount=amt,
            NewBalance=new_balance,
            AccountId=account.Id,
        )

        account.Balance = new_balance

        session.add(tx)
        session.commit()
        return tx

    @staticmethod
    def transfer(from_account_id: int, to_account_id: int, amount) -> tuple[Transaction, Transaction]:
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")

        amt = _to_money(amount) # Gör om input till Decimal och valutagrundvärdet 0.01
        if amt <= Decimal("0"):
            raise InvalidAmountError("Amount must be > 0")

        session = db.session

        # Lås i stabil ordning för att minska deadlocks (lägsta id först) Genom att alltid låsa i samma ordning minskas risken drastiskt.
        first_id, second_id = sorted([from_account_id, to_account_id])
        first = TransactionService._lock_account(session, first_id) # andra transaktioner som vill låsa samma konto måste vänta tills du committar/rollar tillbaka.
        second = TransactionService._lock_account(session, second_id)

        # Mappa tillbaka till from/to
        from_acc = first if first.Id == from_account_id else second
        to_acc = second if from_acc is first else first

        from_balance = _to_money(from_acc.Balance)
        if from_balance < amt:
            raise InsufficientFundsError(from_acc.Id, from_balance, amt)

        new_from = from_balance - amt
        new_to = _to_money(to_acc.Balance) + amt

        # Två transaktioner, samma commit (atomärt)
        tx_out = Transaction(
            Type="DEBIT",
            Operation=f"Transfer to account nr: {to_acc.Id}",
            Date=datetime.now(),
            Amount=amt,
            NewBalance=new_from,
            AccountId=from_acc.Id,
        )

        tx_in = Transaction(
            Type="CREDIT",
            Operation=f"Transfer from account nr: {from_acc.Id}",
            Date=datetime.now(),
            Amount=amt,
            NewBalance=new_to,
            AccountId=to_acc.Id,
        )

        from_acc.Balance = new_from
        to_acc.Balance = new_to

        session.add_all([tx_out, tx_in])
        session.commit()

        return tx_out, tx_in

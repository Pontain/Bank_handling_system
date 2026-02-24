from decimal import Decimal
import pytest
from models.model import Account
from services.transaction_service import TransactionService, InvalidAmountError, InsufficientFundsError


def test_withdraw_more_than_balance():

    # Arrange: Skapa ett konto med 200 kr och id 1
    account = Account() # Används som ett pythonobjekt, ej databasmodell
    account.Id = 1
    account.Balance = Decimal("200.00")

    # Act & Assert: Försök ta ut 300 kr, vilket ska ge ett undantag
    with pytest.raises(InsufficientFundsError): # Testet ska bara passera om det kastas ett InsufficientFundsError
        TransactionService.withdraw_logic(account, 300)

    # Assert: Saldo ska fortfarande vara 200 kr
    assert account.Balance == Decimal("200.00")


def test_transfer_more_than_balance():
    from_account = Account()
    from_account.Id = 1
    from_account.Balance = Decimal("200.00")

    to_account = Account()
    to_account.Id = 2
    to_account.Balance = Decimal("100.00")

    with pytest.raises(InsufficientFundsError):
        TransactionService.transfer_logic(from_account, to_account, 300)

    assert from_account.Balance == Decimal("200.00")
    assert to_account.Balance == Decimal("100.00")


def test_deposit_negative_amount():
    account = Account()
    account.Id = 1
    account.Balance = Decimal("200.00")

    with pytest.raises(InvalidAmountError): 
        TransactionService.deposit_logic(account, -50) 

    assert account.Balance == Decimal("200.00")

def test_withdraw_negative_amount():
    account = Account()
    account.Id = 1
    account.Balance = Decimal("200.00")

    with pytest.raises(InvalidAmountError):
        TransactionService.withdraw_logic(account, -50)

    assert account.Balance == Decimal("200.00")

from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from services.account_service import AccountService
from services.transaction_service import TransactionService, InsufficientFundsError, InvalidAmountError
from forms.forms import AccountDepositForm, AccountWithdrawForm, AccountTransferForm

account_bp = Blueprint("account", __name__, url_prefix="/accounts")


@account_bp.route("/<int:account_id>")
def get_one(account_id: int):
    account = AccountService.get_by_id(account_id)
    if not account:
        abort(404)

    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)
    transactions = AccountService.get_transactions(account_id, limit=limit, offset=offset)

    # Skapa forms och förifyll hidden fields
    deposit_form = AccountDepositForm()
    deposit_form.receiving_account_id.data = account_id

    withdraw_form = AccountWithdrawForm()
    withdraw_form.withdrawing_account_id.data = account_id

    transfer_form = AccountTransferForm()
    transfer_form.withdrawing_account_id.data = account_id

    return render_template(
        "user/account/account.html",
        account=account,
        transactions=transactions,
        deposit_form=deposit_form,
        withdraw_form=withdraw_form,
        transfer_form=transfer_form,
    )


@account_bp.post("/<int:account_id>/deposit")
def deposit(account_id: int):
    form = AccountDepositForm()

    # Lås alltid account-id till URL:en (skydd mot manipulerade hidden fields)
    form.receiving_account_id.data = account_id

    if not form.validate_on_submit():
        flash("Invalid deposit input.", "warning")
        return redirect(url_for("account.get_one", account_id=account_id))

    try:
        TransactionService.deposit(
            account_id=account_id,
            amount=form.amount.data,
            operation="Deposit",
        )
        flash("Deposit completed.", "success")
    except InvalidAmountError as e:
        flash(str(e), "warning")

    return redirect(url_for("account.get_one", account_id=account_id))


@account_bp.post("/<int:account_id>/withdraw")
def withdraw(account_id: int):
    form = AccountWithdrawForm()
    form.withdrawing_account_id.data = account_id

    if not form.validate_on_submit():
        flash("Invalid withdraw input.", "warning")
        return redirect(url_for("account.get_one", account_id=account_id))

    try:
        TransactionService.withdraw(
            account_id=account_id,
            amount=form.amount.data,
            operation="Withdraw",
        )
        flash("Withdraw completed.", "success")
    except InvalidAmountError as e:
        flash(str(e), "warning")
    except InsufficientFundsError as e:
        flash(str(e), "danger")

    return redirect(url_for("account.get_one", account_id=account_id))


@account_bp.post("/<int:account_id>/transfer")
def transfer(account_id: int):
    form = AccountTransferForm()
    form.withdrawing_account_id.data = account_id

    if not form.validate_on_submit():
        # Här hamnar t.ex. "Cannot transfer to the same account."
        flash("Invalid transfer input.", "warning")
        return redirect(url_for("account.get_one", account_id=account_id))

    try:
        TransactionService.transfer(
            from_account_id=account_id,
            to_account_id=form.receiving_account_id.data,
            amount=form.amount.data,
        )
        flash("Transfer completed.", "success")
    except InvalidAmountError as e:
        flash(str(e), "warning")
    except InsufficientFundsError as e:
        flash(str(e), "danger")
    except ValueError as e:
        flash(str(e), "warning")

    return redirect(url_for("account.get_one", account_id=account_id))

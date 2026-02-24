from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_security.decorators import auth_required, roles_required
from services.account_service import AccountService
from services.transaction_service import TransactionService, InsufficientFundsError, InvalidAmountError
from forms.forms import AccountDepositForm, AccountWithdrawForm, AccountTransferForm

account_bp = Blueprint("account", __name__, url_prefix="/accounts")


@account_bp.route("/<int:account_id>")
@auth_required()
@roles_required("CASHIER")
def get_one(account_id: int):
    account = AccountService.get_by_id(account_id)
    if not account:
        abort(404)

    page_size = 20
    offset = 0

    transactions = AccountService.get_transactions(account_id, limit=page_size + 1, offset=offset)

    has_more = len(transactions) > page_size
    transactions = transactions[:page_size]  # trim extra transaction used for has_more check

    # Skapa forms och förifyll hidden fields
    deposit_form = AccountDepositForm()
    deposit_form.receiving_account_id.data = str(account_id)

    withdraw_form = AccountWithdrawForm()
    withdraw_form.withdrawing_account_id.data = str(account_id)

    transfer_form = AccountTransferForm()
    transfer_form.withdrawing_account_id.data = str(account_id)

    return render_template(
        "user/account/account.html",
        account=account,
        transactions=transactions,
        deposit_form=deposit_form,
        withdraw_form=withdraw_form,
        transfer_form=transfer_form,
        has_more=has_more
    )


@account_bp.post("/<int:account_id>/deposit")
@auth_required()
@roles_required("CASHIER")
def deposit(account_id: int):
    form = AccountDepositForm()

    # Lås alltid account-id till URL:en (skydd mot manipulerade hidden fields)
    form.receiving_account_id.data = str(account_id)

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
@auth_required()
@roles_required("CASHIER")
def withdraw(account_id: int):
    form = AccountWithdrawForm()
    form.withdrawing_account_id.data = str(account_id)

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
@auth_required()
@roles_required("CASHIER")
def transfer(account_id: int):
    form = AccountTransferForm()
    form.withdrawing_account_id.data = str(account_id)

    if not form.validate_on_submit():
        # Här hamnar t.ex. "Cannot transfer to the same account."
        flash("Invalid transfer input.", "warning")
        return redirect(url_for("account.get_one", account_id=account_id))

    try:

        to_account_id_raw = form.receiving_account_id.data
        if not to_account_id_raw:
            flash("Missing receiving account id.", "warning")
            return redirect(url_for("account.get_one", account_id=account_id))

        to_account_id = int(to_account_id_raw)

        TransactionService.transfer(
            from_account_id=account_id,
            to_account_id=to_account_id,
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

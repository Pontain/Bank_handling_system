from flask import Blueprint, render_template, abort, request
from services.account_service import AccountService

account_bp = Blueprint("account", __name__, url_prefix="/accounts")

@account_bp.route("/<int:account_id>")

def get_one(account_id: int):
    account = AccountService.get_by_id(account_id)
    if not account:
        abort(404)

    # Förberett för framtida AJAX
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    transactions = AccountService.get_transactions(account_id, limit=limit, offset=offset)

    return render_template(
        "user/account/account.html",
        account=account,
        transactions=transactions
    )
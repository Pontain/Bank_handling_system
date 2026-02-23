from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_security.decorators import auth_required, roles_required

from services.account_service import AccountService

accounts_api = Blueprint("accounts_api", __name__, url_prefix="/api/accounts")


def _tx_to_dict(tx) -> dict:
    return {
        "Id": tx.Id,
        "Type": tx.Type,
        "Operation": tx.Operation,
        "Date": tx.Date.strftime("%Y-%m-%d %H:%M:%S"),
        "Amount": str(tx.Amount),
        "NewBalance": str(tx.NewBalance),
        "AccountId": tx.AccountId,
    }


@accounts_api.get("/<int:account_id>")
@auth_required()
@roles_required("CASHIER")
def get_account_transactions(account_id: int):

    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)

    txs = AccountService.get_transactions(account_id, limit=limit, offset=offset)

    return jsonify({
        "count": len(txs),
        "items": [_tx_to_dict(t) for t in txs],
        "next_offset": offset + len(txs),
        "has_more": len(txs) == limit,
    })
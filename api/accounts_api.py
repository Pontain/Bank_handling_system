from __future__ import annotations

from flask import Blueprint, jsonify, request
from services.account_service import AccountService

accounts_api = Blueprint("accounts_api", __name__, url_prefix="/api/accounts")

def _tx_to_dict(tx) -> dict:
    return {
        "id": tx.Id,
        "type": tx.Type,
        "operation": tx.Operation,
        "date": tx.Date.isoformat() if tx.Date else None,
        "amount": str(tx.Amount),       # bättre än float för pengar
        "new_balance": str(tx.NewBalance),
    }


@accounts_api.get("/<int:account_id>/transactions")
def get_transactions(account_id: int):
    # GET /api/accounts/123/transactions?limit=20&offset=0
    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)

    txs = AccountService.get_transactions(account_id, limit=limit, offset=offset)

    return jsonify({
        "count": len(txs),
        "items": [_tx_to_dict(t) for t in txs],
        "next_offset": offset + len(txs),
        "has_more": len(txs) == limit,  # enkel tumregel
    })
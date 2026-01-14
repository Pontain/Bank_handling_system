from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from flask_mail import Mail, Message

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from app import app
from database import db
from models.model import Customer, Account, Transaction

STATE_FILE = "ml_state.json"
REPORT_TO = "MoneyLaundering@kimmoahola.net"

SINGLE_TX_THRESHOLD = 15000
WINDOW_HOURS = 72
WINDOW_THRESHOLD = 23000

@dataclass(frozen=True) # Skapar en rad i slutrapporten med flaggat konto.
class FlagRow:

    country: str
    customer_id: int
    customer_name: str
    account_id: int
    transaction_id: int
    reason: str


class JsonStateStore:   # Skapar en json-fil som håller reda på var vi slutate sist
                        # och sparar detta per land.
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> dict[str, dict[str, str]]:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def save(self, state: dict[str, dict[str, str]]) -> None:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=1)

    def get_cursor(self, state: dict, country: str) -> tuple[Optional[datetime], Optional[int]]:
         
         c = state.get(country)
         if not c:
            return None, None
         
         last_date = datetime.fromisoformat(c["last_date"])
         last_tx_id = int(c["last_tx_id"])
         return last_date, last_tx_id
    
        # Cursor är last_date och last_transaction (tx) id. Så pekar på var sista kollen skedde.
        # None returneras om landet ej körs

    def set_cursor(self, state: dict, country: str, last_date: datetime, last_tx_id: int) -> None:
        state[country] = {
            "last_date": last_date.isoformat(),
            "last_tx_id": str(last_tx_id)
        }

############################################################################################

# Rule functions:

def rule_single_transaction(tx: Transaction) -> Optional[str]:

    if tx.Amount > SINGLE_TX_THRESHOLD:
        return f"Rule1: Single transaction > {SINGLE_TX_THRESHOLD} (amount={tx.Amount})"
    return None

def rule_72h_total(transactions: list[Transaction]) -> dict[int, str]:

    flagged: dict[int, str] = {}

    start = 0 # index för äldsta trasaktionen i datumfönstret
    window_sum = 0

    for end, tx in enumerate(transactions): # end är senaste transaktionen i datumfönstret, enumerate tar både key och value.
        window_sum += tx.Amount
        window_start_time = tx.Date - timedelta(hours=WINDOW_HOURS) # 72 h bakåt i tiden från senaste tx.

        while start <= end and transactions[start].Date < window_start_time: # tar bort tx som ligger för långt bak om det finns tx där.
            window_sum -= transactions[start].Amount
            start += 1 # flyttar index för start tx framåt

        if window_sum > WINDOW_THRESHOLD:
            flagged[tx.Id] = ( # den tx som gör att summan överskrids rapporteras
                f"Rule2: Total last {WINDOW_HOURS}h > {WINDOW_THRESHOLD} (sum={window_sum})"
            )
    return flagged
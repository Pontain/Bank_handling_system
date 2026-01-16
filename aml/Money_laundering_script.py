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
REPORT_TO_MYSELF = "pontus.orstadius@gmail.com"

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


############################################################################################

# Report / mail functions

def build_report_text(country: str, rows: list[FlagRow]) -> str:    # Bygger ren text som mail-body. Kravet: lista över personer + kontonummer + transaktionsnummer.
                                                                    # (Vi lägger även reason så det går att förstå varför den hamnade där.)
    header = [
        f"Money laundering report for {country}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]                                                                

    if not rows:
        return "\n".join(header + ["No suspicious transactions found"])
    
    lines = header + ["Suspicious items:", ""] # "" = \n

    #Sortering

    rows_sorted = sorted(rows, key=lambda r: (r.customer_id, r.account_id, r.transaction_id)) # Lambda omvandlar listan till en tuple och gör så 
                                                                                                             # rapporten sorteras så att samma kund och konto grupperas tillsammans

    for r in rows_sorted:
        lines.append(
            f"- Customer {r.customer_id} ({r.customer_name}), "
            f"Account {r.account_id}, Transaction {r.transaction_id} | {r.reason}"
        )

    return "\n".join(lines)


############################################################################################

class AmlAnalyzer: # Den här klassen håller ihop hela flödet: laddar state, loopar länder, hämtar transaktioner, kör reglerna, bygger rapporten, skickar mail och uppdaterar state
                
    def __init__(self, mail: Mail, state_store: JsonStateStore) -> None:
        self.mail = mail
        self.state_store = state_store

    def get_countries(self) -> list[str]:

        rows= ( db.session.query(Customer.Country).distinct().all()) # distinct ger enbart unika värden
        return sorted([r[0] for r in rows if r[0]]) # Plockar ut land-strängar, filtrerar bort None och sorterar dem

    
        # Ovan är en list comprehension som är en kortare variant av nedan:

        #         countries = []
        # for r in rows:
        #     if r[0]:
        #         countries.append(r[0])
        # countries = sorted(countries)
        # return countries

    def send_country_email(self, country: str, report_text: str) -> None:

        subject = f"[AML] Suspicious transactions report - {country}"
        msg = Message(subject=subject, recipients=[REPORT_TO], body=report_text)
        self.mail.send(msg)

    def fetch_new_transactions(
            self,
            customer_id: int,
            country: str,
            last_date: Optional[datetime],
            last_tx_id: Optional[int],
    ) -> list[Transaction]: # Hämtar transaktioner för en kund i landet. Om vi har cursor, hämtar vi bara "nya" transaktioner efter senaste körningen.
        
        q = (
            db.session.query(Transaction)
            .join(Account, Transaction.AccountId == Account.Id)
            .join(Customer, Account.CustomerId == Customer.Id) # Behöver två joins för att få med allt.
            .filter(Customer.Id == customer_id)
            .filter(Customer.Country == country)
        )

        if last_date is not None and last_tx_id is not None: # or_ och and_ används för att bygga SQL-logik (inte Python-logik)

            q = q.filter(
                or_(
                    Transaction.Date > last_date,
                    and_(Transaction.Date == last_date, Transaction.Id > last_tx_id), # Nya transaktioner ska antingen ha nytt datum eller ett senare id på samma datum.
                )
            )

        return q.order_by(Transaction.Date.asc(), Transaction.Id.asc()).all()
    

    def analyze_country(
            self,
            country: str,
            last_date: Optional[datetime],
            last_tx_id: Optional[int],
    ) -> tuple[list[FlagRow], Optional[tuple[datetime, int]]]: # Analyserar ett land och returnerar alla flaggade rader och ny cursor för sista transaktionen.
        
        flagged_rows: list[FlagRow] = []
        max_seen_cursor: Optional[tuple[datetime, int]] = None # Curorn uppdateras när den hittar transaktioner

        customers = db.session.query(Customer).filter(Customer.Country == country).all() # Hämtar kunder från ett land

        for cust in customers: # txs är transaktioner som är nya sedan förra körningen.
            txs = self.fetch_new_transactions(
                customer_id=cust.Id,
                country=country,
                last_date=last_date,
                last_tx_id=last_tx_id,
            )

            if not txs: # Hoppar vidare till nästa kund ifall det ej fins några nya trans.
                continue

            last_tx = txs[-1]
            candidate = (last_tx.Date, last_tx.Id) # Kandidat för max cursor
            max_seen_cursor = candidate if max_seen_cursor is None else max(max_seen_cursor, candidate)

            # Regel 1

            for tx in txs:
                r1 = rule_single_transaction(tx)
                if r1:
                    flagged_rows.append(
                        FlagRow(
                            country=country,
                            customer_id=cust.Id,
                            customer_name=f"{cust.GivenName} {cust.Surname}",
                            account_id=tx.AccountId,
                            transaction_id=tx.Id,
                            reason=r1,
                        )
                    )

            # Regel 2

            r2_results = rule_72h_total(txs)
            if r2_results:
                for tx in txs:
                    if tx.Id in r2_results:
                        flagged_rows.append(
                            FlagRow(
                                country=country,
                                customer_id=cust.Id,
                                customer_name=f"{cust.GivenName} {cust.Surname}",
                                account_id=tx.AccountId,
                                transaction_id=tx.Id,
                                reason=r2_results[tx.Id],
                            )
                        )

        return flagged_rows, max_seen_cursor
    
    def run(self) -> None: # Här laddas state, loopar länder, analyserar länder, skickar mail och sparar ny cursor.

        state = self.state_store.load()
        countries = self.get_countries()

        for country in countries:
            last_date, last_tx_id = self.state_store.get_cursor(state, country)

            rows, new_cursor = self.analyze_country(country, last_date, last_tx_id)

            report_text = build_report_text(country, rows)
            self.send_country_email(country, report_text)

            if new_cursor is not None:
                new_date, new_id = new_cursor
                self.state_store.set_cursor(state, country, new_date, new_id)

        self.state_store.save(state)


############################################################################################

# Körning

def main() -> None:

    mail = Mail(app)

    with app.app_context():
        analyzer = AmlAnalyzer(
            mail=mail,
            state_store=JsonStateStore(STATE_FILE),
        )
        analyzer.run()

############################################################################################

# def test_mail() -> None:
#     mail = Mail(app)
#     with app.app_context():
#         mail.send(
#             Message(
#                 subject="AML test mail",
#                 recipients=[REPORT_TO_MYSELF],
#                 body="This is a test email from the AML script."
#             )
#         )


if __name__ == "__main__":
    main()
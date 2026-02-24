# pyright: reportIncompatibleVariableOverride=false
import random
from datetime import datetime, timedelta, date
from flask_security.utils import hash_password
from faker import Faker
from models.model import Customer, Account, AccountType, Transaction


def seedData(db):
    locales = {"SV": "sv_SE", "DK": "da_DK", "NO": "no_NO", "FI": "fi_FI"}
    antal = db.session.query(Customer).count()
    countries = ["SV", "DK", "NO", "FI"]

    while antal < 5000:
        customer = Customer()
        country = random.choice(countries)
        locale = locales[country]
        fake = Faker(locale)

        # Generate names
        customer.GivenName = fake.first_name()
        customer.Surname = fake.last_name()

        # Address
        customer.Streetaddress = fake.street_address()
        customer.Zipcode = fake.postcode()
        customer.City = fake.city()
        customer.Country = random.choice(countries)
        customer.CountryCode = random.choice(countries)

        # Birthday & NationalId
        birthday = date.fromisoformat(
            fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
        )

        customer.Birthday = birthday
        cc_number: int = fake.random_number(digits=4, fix_len=True)
        customer.NationalId = birthday.strftime("%Y%m%d-") + str(cc_number)

        # Phone & Email
        customer.Telephone = fake.phone_number()
        customer.EmailAddress = fake.email().lower()

        # Accounts
        for _ in range(random.randint(1, 4)):
            account = Account()

            c = random.randint(0, 100)
            if c < 33:
                account.AccountType = AccountType.PERSONAL
            elif c < 66:
                account.AccountType = AccountType.CHECKING
            else:
                account.AccountType = AccountType.SAVINGS

            start = datetime.now() + timedelta(days=-random.randint(1000, 10000))
            account.created_at = start
            account.Balance = 0

            # Transactions
            for _ in range(random.randint(0, 30)):
                tran = Transaction()
                start = start + timedelta(days=-random.randint(10, 100))
                if start > datetime.now():
                    break
                tran.Date = start

                belopp = random.randint(0, 30) * 100
                tran.Amount = belopp

                # Determine debit/credit
                if account.Balance - belopp < 0:
                    tran.Type = "Debit"
                else:
                    tran.Type = "Credit" if random.randint(0, 100) > 70 else "Debit"

                # Operations
                r = random.randint(0, 100)
                if tran.Type == "Debit":
                    account.Balance += belopp
                    if r < 20:
                        tran.Operation = "Deposit cash"
                    elif r < 66:
                        tran.Operation = "Salary"
                    else:
                        tran.Operation = "Transfer"
                else:
                    account.Balance -= belopp
                    if r < 40:
                        tran.Operation = "ATM withdrawal"
                    elif r < 75:
                        tran.Operation = "Payment"
                    elif r < 85:
                        tran.Operation = "Bank withdrawal"
                    else:
                        tran.Operation = "Transfer"

                tran.NewBalance = account.Balance
                account.Transactions.append(tran)

            customer.Accounts.append(account)

        db.session.add(customer)
        antal += 1

    db.session.commit()


def seed_security_staff(db, user_datastore):
    # Skapa roller
    for role_name, desc in [
        ("ADMIN", "Admin handles employees"),
        ("CASHIER", "Cashier handles accounts and transactions"),
    ]:
        user_datastore.find_or_create_role(
            name=role_name,
            description=desc,
        )

    db.session.commit()

    admin_role = user_datastore.find_role("ADMIN")
    cashier_role = user_datastore.find_role("CASHIER")

    # Admin
    if not user_datastore.find_user(email="admin@test.se"):
        user_datastore.create_user(
            email="admin@test.se",
            username="Admin",
            password=hash_password("Hejsan123!"),
            roles=[admin_role],
        )

    # Cashier
    if not user_datastore.find_user(email="cashier@test.se"):
        user_datastore.create_user(
            email="cashier@test.se",
            username="Cashier",
            password=hash_password("Hejsan123!"),
            roles=[cashier_role],
        )

    # Supervisor (båda rollerna)
    if not user_datastore.find_user(email="supervisor@test.se"):
        user_datastore.create_user(
            email="supervisor@test.se",
            username="Supervisor",
            password=hash_password("Hejsan123!"),
            roles=[admin_role, cashier_role],
        )

    # Kimmo-Admin
    if not user_datastore.find_user(email="kimmo.ahola@systementor.se"):
        user_datastore.create_user(
            email="kimmo.ahola@systementor.se",
            username="Kimmo-Admin",
            password=hash_password("Hejsan123!"),
            roles=[admin_role],
        )

    # Kimmo-Cashier
    if not user_datastore.find_user(email="kimmo.ahola@webbramverk.se"):
        user_datastore.create_user(
            email="kimmo.ahola@webbramverk.se",
            username="Kimmo-Cashier",
            password=hash_password("Hejsan123!"),
            roles=[cashier_role],
        )

    db.session.commit()

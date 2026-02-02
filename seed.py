from datetime import datetime, timedelta
import random
from faker import Faker
from models.model import Customer, Account, AccountType, Transaction, StaffUser, StaffRole
from sqlalchemy import select
from database import db


def seedData(db):
    locales = {"SV": "sv_SE", "DK": "da_DK", "NO": "no_NO", "FI": "fi_FI"}
    antal = db.session.query(Customer).count()
    countries = ["SV", "DK", "NO", "FI"]

    while antal < 1000:
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
        customer.Birthday = fake.date_of_birth(minimum_age=18, maximum_age=90)
        cc_number = fake.random_number(digits=4, fix_len=True)
        customer.NationalId = customer.Birthday.strftime("%Y%m%d-") + str(cc_number)

        # Phone & Email
        customer.TelephoneCountryCode = 55
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
            account.Created = start
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

from database import db
from models.model import StaffUser, StaffRole
from sqlalchemy import select

def seed_staff():


    staff_data = [
        ("admin", [StaffRole.ADMIN]),
        ("cashier1", [StaffRole.CASHIER]),
        ("cashier2", [StaffRole.CASHIER]),
        ("supervisor", [StaffRole.ADMIN, StaffRole.CASHIER]),  # exempel på flera roller
        ("inactive_cashier", [StaffRole.CASHIER]),
    ]

    try:
        for username, roles in staff_data:
            # Finns användaren redan?
            stmt = select(StaffUser).where(StaffUser.Username == username)
            user = db.session.execute(stmt).scalars().first()

            if not user:
                user = StaffUser(Username=username, PasswordHash=None, IsActive=True)
                db.session.add(user)
                db.session.flush()  # ger user.Id

            # Exempel: en av dem ska vara inaktiv
            if username == "inactive_cashier":
                user.IsActive = False

            # Sätt roller (add_role skyddar mot dubletter)
            for r in roles:
                user.add_role(r)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

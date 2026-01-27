from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, Regexp, NumberRange, ValidationError
from dateutil import relativedelta


def is_adult():
    
    def _is_adult(form, field):
        if field.data is None:

            raise ValidationError("Date of birth is required")

        today = date.today()
        delta = relativedelta.relativedelta(today, field.data)

        if delta.years < 18:
            raise ValidationError("You must be at least 18 years old")

    return _is_adult


class AccountDepositForm(FlaskForm):
    receiving_account_id = HiddenField(validators=[DataRequired()]) # Så du inte kan posta formuläret utan konto-id. Annars kan någon få None och du får konstiga fel
    amount = DecimalField(
        "Amount",
        places=2, # Det gör att fältet hanterar 2 decimaler snyggt vid rendering och parsing.
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be at least 0.01")],
            render_kw={"Placeholder": "Amount"}
    )
    submit = SubmitField("Deposit")


class AccountWithdrawForm(FlaskForm):
    withdrawing_account_id = HiddenField(validators=[DataRequired()])
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be at least 0.01")],
            render_kw={"Placeholder": "Amount"}
    )
    submit = SubmitField("Withdraw")


class AccountTransferForm(FlaskForm):
    withdrawing_account_id = HiddenField(validators=[DataRequired()])
    receiving_account_id = IntegerField("To account Id", validators=[DataRequired(), NumberRange(min=1)],
                                        render_kw={"placeholder": "To account id"}
                                        )
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be at least 0.01"),
        ],render_kw={"Placeholder": "Amount"}
    )
    submit = SubmitField("Transfer")

    def validate_receiving_account_id(self, field):
        # WTForms kör denna automatiskt när du kallar form.validate_on_submit()
        # validate_<fieldname> = “Extra regler som ska gälla just för detta fält” WTForms letar aktivt efter dem varje gång du validerar.
        if str(field.data) == str(self.withdrawing_account_id.data):
            raise ValidationError("Cannot transfer to the same account.")


class CustomerCreateForm(FlaskForm):
    # --- Names ---
    given_name = StringField(
        "Given name",
        validators=[DataRequired(), Length(min=1, max=50)],
    )

    surname = StringField(
        "Surname",
        validators=[DataRequired(), Length(min=1, max=50)],
    )

    # --- Address ---
    streetaddress = StringField(
        "Street address",
        validators=[DataRequired(), Length(min=1, max=50)],
    )

    city = StringField(
        "City",
        validators=[DataRequired(), Length(min=1, max=50)],
    )

    zipcode = StringField(
        "Zip code",
        validators=[
            DataRequired(),
            Length(min=3, max=10),
            Regexp(r"^[0-9A-Za-z\- ]+$", message="Invalid zip code format"),
        ],
    )

    country = StringField(
        "Country",
        validators=[DataRequired(), Length(min=2, max=30)],
    )

    country_code = StringField(
        "Country code (ISO)",
        validators=[
            DataRequired(),
            Length(min=2, max=2),
            Regexp(r"^[A-Z]{2}$", message="Use ISO country code, e.g. SE"),
        ],
    )

    # --- Personal info ---
    birthday = DateField(
        "Date of birth",
        validators=[DataRequired(), is_adult()],
        render_kw={"max": date.today().isoformat()},
    )

    national_id = StringField(
        "National ID",
        validators=[
            DataRequired(),
            Length(min=6, max=20),
            Regexp(r"^[0-9\-]+$", message="Invalid national ID format"),
        ],
    )

    # --- Contact ---

    telephone = StringField(
        "Telephone number",
        validators=[
            DataRequired(),
            Length(min=5, max=20),
            Regexp(r"^[0-9+\-\s()]+$", message="Telephone may contain digits, +, spaces, - and ()"),
        ],
    )

    email = StringField(
        "Email address",
        validators=[
            DataRequired(),
            Length(min=5, max=50),
            Regexp(
                r"^[^@]+@[^@]+\.[^@]+$",
                message="Invalid email address",
            ),
        ],
    )

    submit = SubmitField("Create customer")

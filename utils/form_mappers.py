
from datetime import datetime
from models.model import Customer
from forms.forms import CustomerCreateForm


def prefill_customer_form(form: CustomerCreateForm, customer: Customer) -> None:
    """Fill WTForm fields from Customer model (for edit view)."""

    form.given_name.data = customer.GivenName
    form.surname.data = customer.Surname
    form.streetaddress.data = customer.Streetaddress
    form.city.data = customer.City
    form.zipcode.data = customer.Zipcode
    form.country.data = customer.Country
    form.country_code.data = customer.CountryCode

    # DateField expects date, model has datetime
    form.birthday.data = customer.Birthday if customer.Birthday else None

    form.national_id.data = customer.NationalId
    form.telephone.data = customer.Telephone
    form.email.data = customer.EmailAddress


def apply_customer_form(customer: Customer, form: CustomerCreateForm) -> None:

    customer.GivenName = form.given_name.data
    customer.Surname = form.surname.data
    customer.Streetaddress = form.streetaddress.data
    customer.City = form.city.data
    customer.Zipcode = form.zipcode.data
    customer.Country = form.country.data
    customer.CountryCode = form.country_code.data

    # DateField -> datetime
    customer.Birthday = datetime.combine(
        form.birthday.data,
        datetime.min.time()
    )

    customer.NationalId = form.national_id.data
    customer.Telephone = form.telephone.data
    customer.EmailAddress = form.email.data

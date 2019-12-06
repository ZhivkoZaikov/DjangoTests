import datetime

from rest_framework.exceptions import ValidationError


def validate_date_not_in_future(date_of_birth):
    if date_of_birth > datetime.date.today():
            raise ValidationError('Invalid date! Date of birth/death cannot be in the future!')



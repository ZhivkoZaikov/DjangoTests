import datetime

from rest_framework.exceptions import ValidationError


def validate_date_not_in_future(date_of_birth):
    if date_of_birth:
        if date_of_birth > datetime.date.today():
            raise ValidationError('Invalid date logic declaration! Check the dates and reconfigure them accordingly!')



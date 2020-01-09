from django.core.exceptions import ValidationError

# when testing models, validators and serializers are not included
# should I test them too?
# is it correct to test them with full_clean() - by doing so validators in validators.py would be included
# but serializers.py would not be included
# or should I test the declarations in the model only?
# should I create additional validation in models.py (if possible)

# Should I run tests with circleci.com or other?

# Documentation? coreapi? swagger? other?




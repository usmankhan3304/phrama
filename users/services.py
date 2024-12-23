from typing import Optional, Tuple
from django.db import transaction
from .models import CustomUser


def user_create(email, password=None, **extra_fields) -> CustomUser:
    extra_fields = {
        'is_staff': False,
        'is_superuser': False,
        **extra_fields
    }

    user = CustomUser(email=email, **extra_fields)

    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()

    user.full_clean()
    user.save()

    return user


@transaction.atomic
def user_update(*, user: CustomUser, data: dict) -> CustomUser:
    # Define fields that should be updated
    non_side_effect_fields = {"first_name", "last_name", "email"}
    
    # Update fields if they are in the data dictionary and are allowed to be updated
    for field in non_side_effect_fields:
        if field in data:
            setattr(user, field, data[field])

    # Save the user object to apply changes
    user.save()

    # Any additional processing can be done here

    return user

@transaction.atomic
def user_get_or_create(*, email: str, **extra_data) -> Tuple[CustomUser, bool]:
    user = CustomUser.objects.filter(email=email).first()

    if user:
        return user, False

    return user_create(email=email, **extra_data), True



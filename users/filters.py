import django_filters

from users.models import CustomUser


class CustomUserFilter(django_filters.FilterSet):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "is_admin")
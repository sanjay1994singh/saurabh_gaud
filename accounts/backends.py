from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class EmailPhoneUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get(User.USERNAME_FIELD)
        if not login_value or not password:
            return None

        user = (
            User.objects.filter(Q(username__iexact=login_value) | Q(email__iexact=login_value) | Q(phone=login_value))
            .order_by("pk")
            .first()
        )
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

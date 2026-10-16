"""
Authentication backend for role-based access control.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class CustomAuthenticationBackend(ModelBackend):
    """Custom authentication backend supporting email-based authentication."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate by email.

        The lookup value arrives under different keyword names depending on
        the caller. Django's admin and forms pass ``username`` even when
        ``USERNAME_FIELD`` is ``email``, while Django REST Framework's
        SimpleJWT views pass ``email``. Accepting only one of them means half
        of the login paths silently fail, so resolve the field name from the
        user model and check every plausible keyword.
        """
        identifier = None
        for field in (User.USERNAME_FIELD, 'username', 'email'):
            if field and kwargs.get(field):
                identifier = kwargs[field]
                break
        if identifier is None:
            identifier = username

        if not identifier or not password:
            return None

        user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            # Run the default hasher once so the response time does not reveal
            # whether the account exists.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Backend d'authentification personnalisée.

    Permet aux utilisateurs de se connecter en utilisant soit leur nom d'utilisateur,
    soit leur adresse e-mail.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Essayer de trouver un utilisateur correspondant au nom d'utilisateur OU à l'e-mail.
            # L'utilisation de `__iexact` permet une comparaison insensible à la casse.
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            # Aucun utilisateur trouvé, l'authentification échoue.
            return None

        # Si un utilisateur est trouvé, on vérifie son mot de passe.
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        # Le mot de passe est incorrect, l'authentification échoue.
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Les utilisateurs"

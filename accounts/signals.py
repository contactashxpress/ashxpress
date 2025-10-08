from allauth.account.signals import user_signed_up
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .emails import send_welcome_email

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_welcome_email_on_creation(sender, instance, created, **kwargs):
    if created:
        # Ne rien faire si socialaccount existe
        if hasattr(instance, 'socialaccount_set') and instance.socialaccount_set.exists():
            return
        send_welcome_email(instance.id)
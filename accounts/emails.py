from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from config import settings

User = get_user_model()


def send_welcome_email(user_id):
    """
    Envoie un e-mail de bienvenue à un nouvel utilisateur.
    """
    try:
        user = User.objects.get(id=user_id)
        # Traduction du sujet de l'email
        subject = _("Bienvenue sur Ashxpress !")

        # Le contexte reste le même, la traduction est gérée dans le template
        context = {'user': user}
        html_message = render_to_string('accounts/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )
        print(f"E-mail de bienvenue envoyé à {user.email}")
    except User.DoesNotExist:
        print(f"Erreur : Impossible d'envoyer l'e-mail, utilisateur {user_id} non trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi de l'e-mail de bienvenue : {e}")


def send_password_change_email(user_id):
    """
    Envoie un e-mail de notification après un changement de mot de passe.
    """
    try:
        user = User.objects.get(id=user_id)
        # Traduction du sujet de l'email
        subject = _("Confirmation de changement de mot de passe")

        # Le contexte reste le même, la traduction est gérée dans le template
        context = {'user': user}
        html_message = render_to_string('accounts/emails/password_change_notification.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )
        print(f"E-mail de confirmation de changement de mot de passe envoyé à {user.email}")
    except User.DoesNotExist:
        print(f"Erreur : Impossible d'envoyer l'e-mail, utilisateur {user_id} non trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi de l'e-mail : {e}")
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from config import settings
#from .models import Order
from .models import NewsLetter, Order


# Gestion de notification des commandes
def send_order_notification(order_id, is_new_order=False):
    """
    Envoie un e-mail de notification de commande.
    - Si is_new_order est True, envoie l'e-mail de confirmation.
    - Sinon, envoie un e-mail de mise à jour de statut.
    """
    try:
        order = Order.objects.get(id=order_id)

        if is_new_order:
            subject = _("Votre commande #{} a bien été reçue").format(order.id)
            template_name = 'store/emails/order_confirmation.html'
        else:
            subject = _("Mise à jour du statut de votre commande #{}").format(order.id)
            template_name = 'store/emails/order_status_update.html'

        context = {'order': order}

        # Rendu du template HTML
        html_message = render_to_string(template_name, context)

        # Version texte simple pour les clients de messagerie qui ne supportent pas le HTML
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False
            # Mettez à True en production si vous ne voulez pas qu'une erreur d'e-mail bloque le processus
        )
        print(f"E-mail de notification envoyé pour la commande {order_id}")

    except Order.DoesNotExist:
        print(f"Erreur : Impossible d'envoyer un e-mail, commande {order_id} non trouvée.")
    except Exception as e:
        # En production, il est préférable d'utiliser un système de logging
        print(f"Une erreur critique est survenue lors de l'envoi de l'e-mail pour la commande {order_id}: {e}")

# Gestion de notification abonnements
def send_newsletter_subscription_email(subscription_id):
    """
    Envoie un e-mail de confirmation à un nouvel abonné de la newsletter.
    """
    try:
        subscription = NewsLetter.objects.get(id=subscription_id)
        subject = _("Merci pour votre abonnement à notre newsletter !")

        context = {'subscription': subscription}
        html_message = render_to_string('store/emails/newsletter_subscription.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription.email],
            html_message=html_message,
        )
        print(f"E-mail de confirmation de newsletter envoyé à {subscription.email}")
    except NewsLetter.DoesNotExist:
        print(f"Erreur : Impossible d'envoyer l'e-mail, abonnement {subscription_id} non trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue lors de l'envoi de l'e-mail de newsletter : {e}")



from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.dispatch import receiver
from store.models import Cart, CartItem
from django.db.models.signals import pre_save, post_save
from .models import Order
from .emails import send_order_notification



@receiver(user_logged_in)
@transaction.atomic
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    Fusionne le panier invité dans le panier de l'utilisateur lors de sa connexion.
    """
    # --- MODIFICATION ---
    # On cherche la clé de session de l'invité que nous avons sauvegardée dans la vue
    guest_session_key = request.session.get('guest_session_key')
    if not guest_session_key:
        return  # Pas de session invité à fusionner

    try:
        # On utilise cette clé sauvegardée pour trouver le panier
        guest_cart = Cart.objects.get(session_key=guest_session_key, user=None)
        print(f"Panier invité trouvé (ID: {guest_cart.id}) pour la session {guest_session_key}.")  # Ligne de débogage
    except Cart.DoesNotExist:
        return  # Le panier invité n'existe pas ou est vide, rien à faire

    # Le reste du code est identique
    user_cart, created = Cart.objects.get_or_create(user=user)
    print(f"Panier utilisateur trouvé ou créé (ID: {user_cart.id}).")  # Ligne de débogage

    for guest_item in guest_cart.items.all():
        existing_item, item_created = user_cart.items.get_or_create(
            product=guest_item.product,
            defaults={'quantity': guest_item.quantity}
        )

        if not item_created:
            existing_item.quantity += guest_item.quantity
            existing_item.save()
        print(f"Article '{guest_item.product.name}' fusionné.")  # Ligne de débogage

    # On supprime la clé temporaire de la session et le panier invité
    del request.session['guest_session_key']
    guest_cart.delete()
    print("Fusion terminée. Panier invité supprimé.")  # Ligne de débogage

@receiver(pre_save, sender=Order)
def store_previous_status(sender, instance, **kwargs):
    """
    Avant de sauvegarder un objet Order, on stocke son ancien statut
    pour pouvoir le comparer après la sauvegarde.
    """
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None

@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, **kwargs):
    """
    Après la sauvegarde, si le statut a changé, on envoie un e-mail de notification.
    """
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        print(
            f"Statut de la commande {instance.id} changé de '{instance._old_status}' à '{instance.status}'. Envoi de la notification...")
        send_order_notification(instance.id, is_new_order=False)


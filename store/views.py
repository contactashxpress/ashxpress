from decimal import Decimal
from django.contrib.messages import get_messages
from django.views.decorators.cache import cache_page, never_cache
from cinetpay import Client as Cinetpay, Config, Credential, Channels
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import timedelta
from config import settings
from store.filters import ProductFilter
from store.forms import OrderCreateForm, ReviewForm
from store.models import Product, Category, NewsLetter, Banner, BestSeller, Toast, Promotion, Blog, Cta, CartItem, Cart, \
    Order, OrderItem, ProductLike, ReviewRating, PromoCode
from .emails import send_order_notification, send_newsletter_subscription_email


# Gestion centraliser pour les abboners
def newsletter_subscribe(request):
    """
    Traite la soumission du formulaire d'abonnement à la newsletter.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        next_url = request.POST.get('next', '/')

        if email:
            if NewsLetter.objects.filter(email=email).exists():
                messages.warning(request, "Cette adresse e-mail est déjà abonnée.", extra_tags="newsletter")
            else:
                subscription = NewsLetter.objects.create(email=email)

                # La vue appelle la fonction helper pour faire le travail
                send_newsletter_subscription_email(subscription.id)

                messages.success(request, "Merci ! Votre abonnement a bien été enregistré.", extra_tags="newsletter")
        else:
            messages.error(request, "Veuillez fournir une adresse e-mail valide.", extra_tags="newsletter")

        return redirect(next_url)

    return redirect('index')

# Gestion des produits
#@cache_page(60 * 10) # Cache la page d'accueil pendant 10 minutes
def index(request):
    """
    Vue d'index pour la gestion des produits avec pagination infinie.
    """
    products = Product.objects.select_related('category').prefetch_related('images').all() # OPTIMISÉ
    product_filter = ProductFilter(request.GET, queryset=products)

    # Gestion session_key pour les utilisateurs anonymes
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Configuration de la pagination
    paginator = Paginator(product_filter.qs, 2)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Préchargement des likes pour les produits de la page courante
    if request.user.is_authenticated:
        likes = ProductLike.objects.filter(
            user=request.user,
            product__in=page_obj.object_list
        ).select_related('product') # OPTIMISÉ
    else:
        likes = ProductLike.objects.filter(
            session_key=session_key,
            product__in=page_obj.object_list
        ).select_related('product') # OPTIMISÉ

    liked_product_ids = set(likes.values_list("product_id", flat=True))

    for product in page_obj.object_list:
        product.is_liked = product.id in liked_product_ids

    # Si requête AJAX, retourner uniquement les produits
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products_html = render_to_string("store/partials/product_list.html", {
            "products": page_obj.object_list,
        })
        return JsonResponse({
            "products_html": products_html,
            "has_next": page_obj.has_next(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else 1
        })

    # Featured product (logique existante) - OPTIMISÉ
    featured_product = Product.objects.select_related('category').prefetch_related('images').first()
    if featured_product:
        if request.user.is_authenticated:
            featured_like = ProductLike.objects.filter(
                user=request.user,
                product=featured_product
            ).exists()
        else:
            featured_like = ProductLike.objects.filter(
                session_key=session_key,
                product=featured_product
            ).exists()
        featured_product.is_liked = featured_like

    return render(request, "store/index.html", {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "featured_product": featured_product,
        "filter": product_filter,
        "is_paginated": page_obj.has_other_pages(),
        "page_range": paginator.get_elided_page_range(
            page_obj.number,
            on_each_side=2,
            on_ends=1
        ),
    })


# Gestion du panier
def cart(request):
    cart = get_cart(request)
    items = cart.items.select_related('product').all()

    for item in items:
        item.total_price = item.subtotal

    global_price = Decimal(cart.total_price).quantize(Decimal('0.01'))  # sécurise l'arrondi

    return render(request, "store/cart.html", {
        "items": items,
        "global_price": global_price
    })


# Gestion du recuperation du panier
def get_cart(request):
    """
    Récupère le panier de l'utilisateur (connecté ou non)
    en pré-chargeant le code promo pour optimiser les performances.
    """
    if request.user.is_authenticated:
        # ✅ On ajoute select_related pour l'utilisateur connecté
        cart, _ = Cart.objects.select_related('promo_code').get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        # ✅ On ajoute AUSSI select_related pour l'utilisateur anonyme
        cart, _ = Cart.objects.select_related('promo_code').get_or_create(session_key=session_key)

    return cart


# Gestion du compteur des article directement
# Dan le panier en contournant le cache global
@never_cache
def get_session_data(request):  # ✅ On renomme la fonction
    """
    Fournit les données de session dynamiques (panier, messages)
    pour une mise à jour via JavaScript.
    """
    # --- Logique du panier (inchangée) ---
    cart = get_cart(request)
    cart_items_count = cart.items.count() if cart else 0

    # --- Logique des messages (ajoutée) ---
    messages_data = []
    messages = get_messages(request)
    for message in messages:
        messages_data.append({
            'text': str(message),
            'tags': message.tags,
        })

    # --- Réponse JSON combinée ---
    return JsonResponse({
        'cart_count': cart_items_count,
        'messages': messages_data,
    })


# Gestion d'ajout du produit au panier avec vérification du stock
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = get_cart(request)

    # 1. Vérifier si le produit est en stock
    if not product.is_available:
        messages.error(request, _("Désolé, ce produit est actuellement en rupture de stock."), extra_tags="cart")
        return redirect(request.META.get("HTTP_REFERER", reverse("index")))

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        # Le produit vient d'être ajouté, la quantité est de 1 par défaut, ce qui est correct.
        messages.success(request, _('Le produit a été ajouté à votre panier.'), extra_tags="cart")
    else:
        # 2. Si le produit est déjà dans le panier, vérifier avant d'incrémenter
        if item.quantity < product.stock:
            item.quantity += 1
            item.save()
            messages.success(request, _('La quantité du produit a été mise à jour.'), extra_tags="cart")
        else:
            # La quantité dans le panier atteint déjà le stock maximum
            messages.warning(request,
                             _("Vous ne pouvez pas ajouter plus de cet article, le stock maximum est atteint."),
                             extra_tags="cart")

    return redirect(request.META.get("HTTP_REFERER", reverse("index")))

# Gestion du detail de produit
# + Gestion des commentaires et Evaluations
#@cache_page(60 * 15) # Cache la page d'accueil pendant 15 minutes
def detail(request, slug):
    """
    Version optimisée qui conserve exactement votre logique métier
    """
    # ✅ Prefetch nécessaire pour les images multiples
    product = get_object_or_404(Product.objects.prefetch_related('images', 'features'), slug=slug)

    # ✅ Reviews avec select_related (déjà bon)
    reviews = product.reviews.select_related('user').all()

    can_review = False
    has_reviewed = False
    form = ReviewForm()

    if request.user.is_authenticated:
        # ✅ LOGIQUE IDENTIQUE : Vérification de l'existence d'un review
        user_review_exists = ReviewRating.objects.filter(
            product=product,
            user=request.user
        ).exists()

        if user_review_exists:
            has_reviewed = True
        else:
            # ✅ LOGIQUE IDENTIQUE : Vérification des commandes livrées
            delivered_order_exists = Order.objects.filter(
                user=request.user,
                status=Order.StatusChoices.DELIVERED,
                items__product=product
            ).exists()

            if delivered_order_exists:
                can_review = True

    # ✅ Gestion du formulaire inchangée
    if request.method == 'POST' and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.product = product
            new_review.user = request.user
            new_review.save()
            messages.success(request, _("Merci ! Votre avis a été publié."), extra_tags="detail")
            return redirect('product', slug=product.slug)

    context = {
        'product': product,
        'reviews': reviews,
        'form': form,
        'can_review': can_review,
        'has_reviewed': has_reviewed,
    }
    return render(request, 'store/product_detail.html', context)

# Gestion du decrementation du produit
def decrement(request, item_id):
    cart = get_cart(request)
    try:
        item = cart.items.get(product_id=item_id)
        if item.quantity > 1:
            item.quantity -= 1
            messages.success(request, _('Votre panier a été mis à jour'), extra_tags="cart")
            item.save()
        else:
            item.delete()
            messages.success(request, _('Vous avez supprimé un produit de votre panier'), extra_tags="cart")
    except CartItem.DoesNotExist:
        pass

    return redirect("cart")

# Gestion de la suppression du produit
def delete_item(request, item):
    cart = get_cart(request)  # récupère le panier approprié
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=item)
    cart_item.delete()
    messages.success(request, _('Vous avez supprimé un produit de votre panier'), extra_tags="cart")
    return redirect('cart')

# Gestion de la suppression de tout le produit d'un seul coup
def empty_cart(request):
    cart = get_cart(request)  # récupère le panier approprié
    if cart:
        cart.items.all().delete()
        messages.success(request, _('Votre panier a été vidé avec succès.'), extra_tags="cart")
    return redirect('cart')

# Gestion des codes promos
@require_POST
def apply_promo_code(request):
    code = request.POST.get('promo_code', '').strip()
    cart = get_cart(request)

    if not code:
        # Si l'utilisateur veut retirer le code
        cart.promo_code = None
        cart.save()
        messages.info(request, _("Le code promotionnel a été retiré."), extra_tags="cart")
        return redirect('cart')

    try:
        promo_code = PromoCode.objects.get(code__iexact=code)  # __iexact pour ignorer la casse

        if not promo_code.is_valid():
            messages.error(request, _("Ce code promotionnel n'est pas valide ou a expiré."), extra_tags="cart")
        else:
            cart.promo_code = promo_code
            cart.save()
            messages.success(request, _("Le code promotionnel a été appliqué avec succès !"), extra_tags="cart")

    except PromoCode.DoesNotExist:
        messages.error(request, _("Le code promotionnel saisi est invalide."), extra_tags="cart")

    return redirect('cart')

# Gestion des commandes avec vérification et décrémentation du stock
@transaction.atomic
def create_order(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()

    if not cart or not cart.items.exists():
        messages.warning(request, _("Votre panier est vide."), extra_tags="cart")
        return redirect('cart')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # ✅ 1. VÉRIFICATION FINALE DU STOCK AVANT DE CRÉER LA COMMANDE
            for item in cart.items.all():
                product = item.product
                if product.stock < item.quantity:
                    messages.error(
                        request,
                        _("Stock insuffisant pour {product_name}. Il ne reste que {stock_count} unités. Veuillez mettre à jour votre panier.").format(
                            product_name=product.name,
                            stock_count=product.stock
                        ),
                        extra_tags="cart"
                    )
                    return redirect('cart')

            order = form.save(commit=False)
            order.total_paid = cart.total_price

            if request.user.is_authenticated:
                order.user = request.user
            else:
                if not request.session.session_key:
                    request.session.create()
                order.session_key = request.session.session_key

            if cart.promo_code and cart.promo_code.is_valid():
                order.promo_code = cart.promo_code

            order.save()

            # ✅ 2. CRÉATION DES ARTICLES DE COMMANDE ET DÉCRÉMENTATION DU STOCK
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.current_price,
                    quantity=item.quantity
                )
                # Décrémentation du stock de manière sécurisée (évite les race conditions)
                Product.objects.filter(id=item.product.id).update(stock=F('stock') - item.quantity)

            # On envoie l'e-mail ici pour les tests locaux.
            send_order_notification(order.id, is_new_order=True)

            transaction_id = f"ORDER-{order.id}-{int(timezone.now().timestamp())}"
            order.transaction_id = transaction_id
            order.save(update_fields=['transaction_id'])

            # NOTE: En production, settings.SITE_URL doit être votre nom de domaine
            notify_url = settings.SITE_URL + reverse('cinetpay_notify')
            return_url = settings.SITE_URL + reverse('payment_return')

            credentials = Credential(
                api_key=settings.CINETPAY_API_KEY,
                site_id=int(settings.CINETPAY_SITE_ID),
                secret_key=settings.CINETPAY_SECRET_KEY,
            )
            configs = Config(
                credentials=credentials, currency='XOF', language='fr', channels=Channels.ALL,
                lock_phone_number=False, raise_on_error=False,
                mode='PROD'  # 👈 IMPORTANT: Changer pour 'PROD' en production
            )
            client = Cinetpay(configs)

            payment_data = {
                'amount': int(order.total_paid),
                'currency': 'XOF',
                'transaction_id': transaction_id,
                'description': f'Paiement pour la commande #{order.id}',
                'return_url': return_url,
                'notify_url': notify_url,
                'customer_name': f"{order.first_name} {order.last_name}",
                'customer_surname': order.last_name,
                'customer_email': order.email,
                'customer_phone_number': order.phone,
            }

            try:
                response = client.initialize_transaction(payment_data)
                if response['code'] == '201':
                    payment_link = response['data']['payment_url']
                    request.session['order_id'] = order.id
                    cart.delete()  # Le panier est vidé seulement si le paiement est initié
                    return redirect(payment_link)
                else:
                    # Si CinetPay refuse, la transaction est annulée grâce à @transaction.atomic
                    messages.error(request, _("Le service de paiement a refusé la transaction. Veuillez réessayer."),
                                   extra_tags="cart")
                    return redirect('cart')
            except Exception:
                # Si une erreur survient, la transaction est annulée
                messages.error(request, _("Une erreur technique est survenue. Veuillez réessayer plus tard."),
                               extra_tags="cart")
                return redirect('cart')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {'first_name': request.user.first_name, 'last_name': request.user.last_name,
                            'email': request.user.email}
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'store/create_order.html', {'cart': cart, 'form': form})

#  Gestion des commandes sans panier avec gestion du stock
@transaction.atomic
def create_single_product_order(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # ✅ 1. VÉRIFICATION DU STOCK AVANT D'AFFICHER LE FORMULAIRE
    if not product.is_available:
        messages.error(request, _("Ce produit n'est plus disponible à la vente."), extra_tags="payment")
        return redirect('product', slug=slug)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_paid = product.current_price

            if request.user.is_authenticated:
                order.user = request.user
            else:
                if not request.session.session_key:
                    request.session.create()
                order.session_key = request.session.session_key

            order.save()
            OrderItem.objects.create(order=order, product=product, price=product.current_price, quantity=1)

            # ✅ 2. DÉCRÉMENTATION DU STOCK
            product.stock = F('stock') - 1
            product.save(update_fields=['stock'])

            # 📧 ENVOI DE L'EMAIL DE CONFIRMATION
            send_order_notification(order.id, is_new_order=True)

            transaction_id = f"ORDER-{order.id}-{int(timezone.now().timestamp())}"
            order.transaction_id = transaction_id
            order.save(update_fields=['transaction_id'])

            # NOTE: En production, settings.SITE_URL doit être votre nom de domaine
            notify_url = settings.SITE_URL + reverse('cinetpay_notify')
            return_url = settings.SITE_URL + reverse('payment_return')

            credentials = Credential(
                api_key=settings.CINETPAY_API_KEY,
                site_id=int(settings.CINETPAY_SITE_ID),
                secret_key=settings.CINETPAY_SECRET_KEY,
            )
            configs = Config(
                credentials=credentials, currency='XOF', language='fr', channels=Channels.ALL,
                lock_phone_number=False, raise_on_error=False,
                mode='PROD'  # 👈 IMPORTANT: Changer pour 'PROD' en production
            )
            client = Cinetpay(configs)

            payment_data = {
                'amount': int(order.total_paid), 'currency': 'XOF', 'transaction_id': transaction_id,
                'description': f'Achat direct pour {product.name}', 'return_url': return_url, 'notify_url': notify_url,
                'customer_name': f"{order.first_name} {order.last_name}", 'customer_email': order.email,
                'customer_phone_number': order.phone,
            }

            try:
                response = client.initialize_transaction(payment_data)
                if response['code'] == '201':
                    payment_link = response['data']['payment_url']
                    request.session['order_id'] = order.id
                    return redirect(payment_link)
                else:
                    messages.error(request, _("Le service de paiement a refusé la transaction. Veuillez réessayer."), extra_tags="payment")
                    return redirect('product', slug=slug)
            except Exception:
                messages.error(request, _("Une erreur technique est survenue. Veuillez réessayer plus tard."), extra_tags="payment")
                return redirect('product', slug=slug)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {'first_name': request.user.first_name, 'last_name': request.user.last_name,
                            'email': request.user.email}
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'store/create_order.html', {'product': product, 'form': form})

# Gestion des notifications Cinetpay
@csrf_exempt
def cinetpay_notify(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('cpm_trans_id')
        if not transaction_id:
            return JsonResponse({'status': 'error', 'message': _('ID de transaction manquant')}, status=400)

        try:
            credentials = Credential(
                api_key=settings.CINETPAY_API_KEY,
                site_id=int(settings.CINETPAY_SITE_ID),
                secret_key=settings.CINETPAY_SECRET_KEY,
            )
            configs = Config(
                credentials=credentials, currency='XOF', language='fr', channels=Channels.ALL,
                lock_phone_number=False, raise_on_error=False,
                mode='PROD'  # 👈 IMPORTANT: Changer pour 'PROD' en production
            )
            client = Cinetpay(configs)

            response = client.get_transaction(transaction_id)
            order = Order.objects.get(transaction_id=transaction_id)

            if response.get('code') == '00':
                order.paid = True
                order.status = Order.StatusChoices.PROCESSING
                order.save(update_fields=['paid', 'status'])
                return JsonResponse({'status': 'success'})
            else:
                order.status = Order.StatusChoices.CANCELED
                order.save(update_fields=['status'])
                # 💡 CONSEIL : Ici, vous pourriez implémenter la logique pour remettre les produits en stock
                # en cas d'annulation de paiement.
                # for item in order.items.all():
                #     Product.objects.filter(id=item.product.id).update(stock=F('stock') + item.quantity)
                return JsonResponse({'status': 'failed'})

        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': _('Commande non trouvée')}, status=404)
        except Exception:
            return JsonResponse({'status': 'error', 'message': _('Erreur interne du serveur')}, status=500)
    return JsonResponse({'status': 'error', 'message': _('Méthode non autorisée')}, status=405)

# Gestion de confirmation du payement
def payment_return(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, _("Session expirée ou commande non trouvée."), extra_tags="payment")
        return redirect('index')

    try:
        order = Order.objects.get(id=order_id)
        if order.paid:
            # Le paiement est confirmé, rediriger vers la page de succès
            return redirect('order_created')
        else:
            # Le paiement a échoué, a été annulé ou est en attente de confirmation
            messages.warning(request, _("Votre paiement a été annulé ou a échoué. Veuillez réessayer."), extra_tags="payment")
            # 💡 CONSEIL : Rediriger vers la page de commande pour retenter le paiement serait mieux
            return redirect('cart')
    except Order.DoesNotExist:
        messages.error(request, _("La commande que vous essayez de consulter n'existe pas."), extra_tags="payment")
        return redirect('index')

#  Confirmation de la commande
#@never_cache
def order_created(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('index')

    order = get_object_or_404(Order, id=order_id)
    # 🔹 Optionnel : supprimer l'ID après affichage
    # del request.session['order_id']

    return render(request, 'store/order_created.html', {'order': order})

# Gestion des Likes
def toggle_like(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.user.is_authenticated:
        like, created = ProductLike.objects.get_or_create(product=product, user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        like, created = ProductLike.objects.get_or_create(product=product, session_key=session_key)

    if not created:
        # le like existait → on le supprime (unlike)
        like.delete()
        is_liked = False
        messages.success(request, _("Vous avez disliké ce produit"), extra_tags="likes")
    else:
        is_liked = True
        messages.success(request, _("Vous avez liké ce produit"), extra_tags="likes")

    # 🔹 pour un usage AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"liked": is_liked, "likes_count": product.likes.count()})

    # sinon simple redirection
    return redirect(request.META.get("HTTP_REFERER", "index"))

# Gestion de l'historique des commandes
#@never_cache
@login_required
def order_history(request):
    # 🔑 Récupération de la session_key pour les invités
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # ✅ Commandes pour l'utilisateur connecté OU invité
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user)
    else:
        orders = Order.objects.filter(session_key=session_key)

    orders = orders.order_by('-created_at')

    # ✅ Appliquer les filtres
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')

    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    if date_filter != 'all':
        today = timezone.now().date()
        if date_filter == 'month':
            start_date = today - timedelta(days=30)
        elif date_filter == '3months':
            start_date = today - timedelta(days=90)
        elif date_filter == '6months':
            start_date = today - timedelta(days=180)
        elif date_filter == 'year':
            start_date = today - timedelta(days=365)

        orders = orders.filter(created_at__date__gte=start_date)

    # ✅ Pagination
    paginator = Paginator(orders, 10)  # 10 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'current_status': status_filter,
        'current_date': date_filter,
    }

    return render(request, 'store/order_history.html', context)

# Gestion du details des commandes
#@never_cache
@login_required
def order_detail(request, order_id):
    # 🔑 Récupération de la session_key pour les invités
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # 🔹 Récupération de la commande
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id, session_key=session_key)

    return render(request, 'store/order_detail.html', {'order': order})


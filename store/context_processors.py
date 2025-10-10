from django.utils import timezone
from .models import Category, Banner, Cta, Blog, Toast, BestSeller, Promotion, LegalContent, Cart

def global_context(request):
    """
    Fournit un contexte global et optimisé pour tous les templates.
    """
    # ✅ LA CORRECTION :
    # On laisse Django faire la requête optimisée. Il va intelligemment faire un
    # "WHERE parent_id IN (...)". C'est extrêmement rapide.
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')

    # On récupère les autres éléments nécessaires au base.html
    promotions = Promotion.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    banners = Banner.objects.all()[:3]
    bestsellers = BestSeller.objects.all()[:4]
    toast = Toast.objects.order_by('-add_date').first()
    blogs = Blog.objects.all()[:4]
    cta = Cta.objects.first()

    # Calcul du nombre d'articles dans le panier (votre logique était déjà bonne)
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.items.count()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            if cart:
                cart_count = cart.items.count()

    return {
        'categories': categories,
        'banners': banners,
        'bestsellers': bestsellers,
        'toast': toast,
        'blogs': blogs,
        'cta': cta,
        'promotions': promotions,
        'cart_count': cart_count,
        'legal_pages': LegalContent.objects.all()[:6],
    }


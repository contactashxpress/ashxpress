from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from imagekit.models import ImageSpecField
from mptt.models import MPTTModel, TreeForeignKey
from pilkit.processors import ResizeToFill
from django.utils.translation import gettext_lazy as _

from config import settings


# Gestion des categories
class Category(MPTTModel):
    name = models.CharField(_("Nom"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), unique=True, blank=True)
    category_image = models.FileField(_("Image de la catégorie"), upload_to="vectore_images", blank=True, null=True)
    stock = models.PositiveIntegerField(_("Stock"), blank=True, null=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_("Parent"), db_index=True
    )

    class MPTTMeta:
        order_insertion_by = ['name']
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# Gestion des produits
class Product(models.Model):
    STATUS_CHOICES = (
        ('new', _('Nouveauté')),
        ('on_sale', _('Promotion')),
        ('flash_sale', _('Vente flash')),
        ('best_seller', _('Meilleure vente')),
        ('limited', _('Stock limité')),
        ('back_in_stock', _('De retour en stock')),
        ('preorder', _('Précommande')),
        ('sold_out', _('Rupture de stock')),
    )

    name = models.CharField(_("Nom"), max_length=100)
    subname = models.CharField(_("Sous-nom"), max_length=100, blank=True, null=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    current_price = models.DecimalField(_("Prix actuel"), max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(_("Prix original"), max_digits=10, decimal_places=2, blank=True, null=True)
    badge = models.CharField(_("Badge"), max_length=25, blank=True, null=True)
    stock = models.PositiveIntegerField(_("Stock"), default=0)
    thumbnail = models.ImageField(_("Image miniature"), upload_to="products")
    scroll_image = models.ImageField(_("Image défilante"), upload_to="products", blank=True, null=True)
    status = models.CharField(_("Statut"), max_length=25, choices=STATUS_CHOICES, blank=True, null=True, db_index=True)
    category = models.ForeignKey(Category, verbose_name=_("Catégorie"), on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="products", db_index=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    add_date = models.DateTimeField(_("Date d'ajout"), auto_now_add=True, db_index=True)
    # Images optimisées
    product_image = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFill(1280, 813)],
        format="JPEG",
        options={"quality": 90}
    )

    product_scroll_image = ImageSpecField(
        source="scroll_image",
        processors=[ResizeToFill(1280, 813)],
        format="JPEG",
        options={"quality": 90}
    )

    detail_image = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFill(1280, 813)],
        format="JPEG",
        options={"quality": 90}
    )

    cart_image = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFill(75, 75)],
        format="JPEG",
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['-add_date']
        indexes = [
            models.Index(fields=['status', '-add_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display() if self.status else _('Sans statut')}"

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            self.slug = original_slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    # ✅ NOUVELLE PROPRIÉTÉ POUR VÉRIFIER LE STOCK FACILEMENT
    @property
    def is_available(self):
        """Vérifie si le produit est en stock."""
        return self.stock > 0

# Gestion des miniatures de produit
class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name=_("Produit"), on_delete=models.CASCADE, related_name="images", db_index=True)
    image = models.ImageField(_("Image"), upload_to="galerie", blank=True, null=True)
    legende = models.CharField(_("Légende"), max_length=100, blank=True, null=True)
    miniature = ImageSpecField(
        source="image",
        processors=[ResizeToFill(65, 65)],
        format="JPEG",
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Miniature de produit")
        verbose_name_plural = _("Miniatures de produit")

    def __str__(self):
        return f"{_('Miniature pour')} {self.product.name}"

# Gestion des carasteristique de produit
class ProductFeature(models.Model):
    product = models.ForeignKey(Product, verbose_name=_("Produit"), on_delete=models.CASCADE, related_name="features", db_index=True)
    name = models.CharField(_("Nom"), max_length=50, blank=True, null=True)
    value = models.CharField(_("Valeur"), max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("Caractéristique de produit")
        verbose_name_plural = _("Caractéristiques de produit")

    def __str__(self):
        return f"{_('Caractéristique pour')} {self.product.name}"

# Gestion des abonnées par e-mail
class NewsLetter(models.Model):
    email = models.EmailField(_("E-mail"), unique=True)
    subscribed_at = models.DateTimeField(_("Abonné le"), auto_now_add=True)

    class Meta:
        verbose_name = _("Abonnement")
        verbose_name_plural = _("Liste des abonnés")

    def __str__(self):
        return f"{_('L\'adresse e-mail')}: ({self.email}) {_('s\'est abonné le')} {self.subscribed_at.strftime('%d-%m-%Y %H:%M')}"

# Gestion du bannier
class Banner(models.Model):
    banner_title = models.CharField(_("Titre du bandeau"), max_length=100)
    image_banner = models.ImageField(_("Image du bandeau"), upload_to="banner_images")
    description = models.TextField(_("Description"))
    banner_price = models.DecimalField(_("Prix du bandeau"), max_digits=10, decimal_places=2, default=0.00)
    banner_image = ImageSpecField(
        source="image_banner",
        processors=[ResizeToFill(1400, 900)],
        format="JPEG",
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Bandeau")
        verbose_name_plural = _("Bandeaux")

    def __str__(self):
        return self.banner_title

# Gestion des meilleures ventes
class BestSeller(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    current_price = models.DecimalField(_("Prix actuel"), max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(_("Prix original"), max_digits=10, decimal_places=2, blank=True, null=True)
    bestseller_image = models.ImageField(_("Image BestSeller"), upload_to="bestseller_images", blank=True, null=True)
    miniature_bestseller = ImageSpecField(
        source='bestseller_image',
        processors=[ResizeToFill(30, 30)],
        format='JPEG',
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Meilleure vente")
        verbose_name_plural = _("Meilleures ventes")

    def __str__(self):
        return f"{_('Meilleures ventes')} {self.name}"

# Gestion du toast
class Toast(models.Model):
    name = models.CharField(_("Nom"), max_length=100, help_text=_("(Nom du dernier produit vendu)"))
    toast_image = models.ImageField(_("Image du toast"), upload_to="toast_images")
    add_date = models.DateTimeField(_("Date d'ajout"), auto_now_add=True)

    class Meta:
        verbose_name = _("Toast")
        verbose_name_plural = _("Toasts")

    def __str__(self):
        return f"{_('Miniature de Toast')} {self.name}"

# Gestion des blogs descriptifs
class Blog(models.Model):
    name = models.CharField(_("Nom"), max_length=50)
    blog_image = models.ImageField(_("Image du blog"), upload_to="blogs", blank=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    signature = models.CharField(
        _("Signature"), max_length=75, blank=True, null=True,
        help_text=_("(By Mr Admin / August 24, 2025)")
    )
    miniature_blog = ImageSpecField(
        source="blog_image",
        processors=[ResizeToFill(736, 368)],
        format="JPEG",
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Blog")
        verbose_name_plural = _("Blogs")

    def __str__(self):
        return self.name

# Gestion du CTA
class Cta(models.Model):
    cta_discount = models.CharField(_("Remise CTA"), max_length=25)
    cta_title = models.CharField(_("Titre CTA"), max_length=25)
    cta_price = models.DecimalField(_("Prix CTA"), max_digits=10, decimal_places=2, default=0.00)
    cta_image = models.ImageField(_("Image CTA"), upload_to='cta_images')
    cta_banner = ImageSpecField(
        source='cta_image',
        processors=[ResizeToFill(626, 417)],
        format='JPEG',
        options={'quality': 90}
    )

    class Meta:
        verbose_name = _("CTA")
        verbose_name_plural = _("CTAs")

    def __str__(self):
        return self.cta_title

# Gestion de promotion
class Promotion(models.Model):
    name = models.CharField(_("Nom"), max_length=100)
    promotion_image = models.ImageField(_("Image de la promotion"), upload_to="deal_images", blank=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    current_price = models.DecimalField(_("Prix actuel"), max_digits=10, decimal_places=2, default=0.00)
    original_price = models.DecimalField(_("Prix original"), max_digits=10, decimal_places=2, blank=True, null=True)
    already_sold = models.PositiveIntegerField(_("Déjà vendu"), default=0)
    available = models.PositiveIntegerField(_("Stock"), default=0)
    start_date = models.DateTimeField(_("Date de début"), default=timezone.now)
    end_date = models.DateTimeField(_("Date de fin"))
    promo_image = ImageSpecField(
        source="promotion_image",
        processors=[ResizeToFill(800, 700)],
        format="JPEG",
        options={"quality": 90}
    )

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

# Gestion des code promo
class PromoCode(models.Model):
    code = models.CharField(_("Code promo"), max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(
        _("Pourcentage de réduction"),
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text=_("La réduction en pourcentage")
    )
    start_date = models.DateTimeField(_("Date de début"))
    end_date = models.DateTimeField(_("Date de fin"))
    is_active = models.BooleanField(_("Actif"), default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return self.code

    def clean(self):
        """ Assure que la date de fin n'est pas antérieure à la date de début. """
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(_("La date de fin ne peut pas être antérieure à la date de début."))

    def is_valid(self):
        """ Vérifie si le code est actuellement valide. """
        now = timezone.now()
        return self.is_active and self.start_date <= now and self.end_date >= now

# Gestion du panier
class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True, null=True,
        verbose_name=_("Utilisateur"), db_index=True
    )  # si connecté
    session_key = models.CharField(
        _("Clé de session"), max_length=40, blank=True, null=True, unique=True
    )  # si invité
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True, db_index=True)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,  # On ne supprime pas le panier si le code est supprimé
        null=True,
        blank=True,
        related_name='carts', db_index=True
    )

    class Meta:
        verbose_name = _("Panier")
        verbose_name_plural = _("Paniers")

    def __str__(self):
        if self.user:
            return f"{_('Panier de')} {self.user.username}"
        return f"{_('Panier invité')} ({self.session_key})"

    @property
    def subtotal(self):
        """ Le total avant réduction. """
        return sum(item.subtotal for item in self.items.all())

    @property
    def discount_amount(self):
        """ Le montant de la réduction. """
        if self.promo_code and self.promo_code.is_valid():
            return (self.subtotal * self.promo_code.discount_percentage) / 100
        return 0

    @property
    def total_price(self):
        """ Le total final après réduction. """
        return self.subtotal - self.discount_amount

# Gestion du produit dans le panier
class CartItem(models.Model):
    cart = models.ForeignKey(
        "Cart", related_name="items", on_delete=models.CASCADE, verbose_name=_("Panier"), db_index=True
    )
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, verbose_name=_("Produit"), db_index=True
    )
    quantity = models.PositiveIntegerField(_("Quantité"), default=1)

    class Meta:
        verbose_name = _("Article du panier")
        verbose_name_plural = _("Articles du panier")
        # ✅ NOUVELLE CONTRAINTE POUR GARANTIR L'UNICITÉ
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.product.current_price * self.quantity

    # ✅ NOUVELLE MÉTHODE DE VALIDATION DU STOCK
    def clean(self):
        """
        Vérifie que la quantité demandée ne dépasse pas le stock disponible.
        """
        if self.product.stock < self.quantity:
            raise ValidationError(
                _('La quantité demandée pour "%(product)s" dépasse le stock disponible (%(stock)s restants).'),
                code='insufficient_stock',
                params={'product': self.product.name, 'stock': self.product.stock},
            )

# Gestion de la commande.
class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        PROCESSING = 'processing', _('En traitement')
        SHIPPED = 'shipped', _('Expédiée')
        DELIVERED = 'delivered', _('Livrée')
        CANCELED = 'canceled', _('Annulée')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name=_("Utilisateur"), db_index=True
    )
    session_key = models.CharField(_("Clé de session"), max_length=40, null=True, blank=True)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,  # On garde une trace même si le code est supprimé plus tard
        null=True,
        blank=True,
        related_name='orders', db_index=True
    )

    # Informations de contact et de livraison
    first_name = models.CharField(_("Prénom"), max_length=100)
    last_name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("E-mail"))
    phone = models.CharField(_("Téléphone"), max_length=20)
    address = models.CharField(_("Adresse"), max_length=100)
    postal_code = models.CharField(_("Code postal"), max_length=20)
    city = models.CharField(_("Ville"), max_length=100)

    # Informations sur la commande
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    status = models.CharField(
        _("Statut"), max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, db_index=True
    )
    total_paid = models.DecimalField(_("Total payé"), max_digits=10, decimal_places=2, default=0.00)

    # Pour le suivi du paiement (par ex. avec Stripe ou autre)
    paid = models.BooleanField(_("Payé"), default=False, db_index=True)
    transaction_id = models.CharField(_("ID de transaction"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")
        ordering = ('-created_at',)

    def __str__(self):
        return f"{_('Commande')} {self.id} {_('par')} {self.first_name} {self.last_name} - {self.get_status_display()}"

    def get_subtotal(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_tax(self):
        return self.get_subtotal() * settings.TAX_RATE  # Exemple TVA 20%

    def get_total(self):
        return self.get_subtotal() + self.get_tax()

    def get_discount_amount(self):
        """ Calcule le montant de la réduction si un code promo a été utilisé. """
        if self.promo_code:
            return self.get_subtotal() * (Decimal(self.promo_code.discount_percentage) / Decimal("100"))
        return Decimal("0")

# Gestion des articles commandee.
class OrderItem(models.Model):
    order = models.ForeignKey(
        "Order", related_name='items', on_delete=models.CASCADE, verbose_name=_("Commande"), db_index=True
    )
    product = models.ForeignKey(
        'Product', related_name='order_items', on_delete=models.SET_NULL, null=True, verbose_name=_("Produit"), db_index=True
    )
    price = models.DecimalField(_("Prix"), max_digits=10, decimal_places=2)  # Prix au moment de l'achat
    quantity = models.PositiveIntegerField(_("Quantité"), default=1)

    class Meta:
        verbose_name = _("Produit commandé")
        verbose_name_plural = _("Produits commandés")

    def __str__(self):
        username = self.order.user.username if self.order.user else _("Invité")
        product_name = self.product.name if self.product else _("Produit supprimé")
        return f"{username} {_('a commandé')} ({self.quantity}) - {product_name}"

    def get_cost(self):
        return self.price * self.quantity

# Gestion des Likes
class ProductLike(models.Model):
    product = models.ForeignKey(
        "Product", related_name="likes", on_delete=models.CASCADE, verbose_name=_("Produit"), db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Utilisateur"), db_index=True
    )
    session_key = models.CharField(_("Clé de session"), max_length=40, null=True, blank=True)  # pour les invités
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        unique_together = ("product", "user", "session_key")  # évite les doublons
        verbose_name = _("Like de produit")
        verbose_name_plural = _("Likes de produits")

    def __str__(self):
        if self.user:
            return f"{self.user.username} {_('a aimé')} {self.product.name}"
        return f"{_('Invité')} ({self.session_key}) {_('a aimé')} {self.product.name}"

    def clean(self):
        # Validation pour un invité
        if self.user is None and self.session_key:
            if ProductLike.objects.filter(
                    product=self.product,
                    user=None,
                    session_key=self.session_key
            ).exists():
                raise ValidationError(
                    _("Un invité avec cette session a déjà aimé ce produit.")
                )
        # Validation pour un utilisateur
        if self.user is not None:
            if ProductLike.objects.filter(
                    product=self.product,
                    user=self.user
            ).exists():
                raise ValidationError(
                    _("Cet utilisateur a déjà aimé ce produit.")
                )

    def save(self, *args, **kwargs):
        self.full_clean()  # déclenche clean() avant l'enregistrement
        super().save(*args, **kwargs)

# Gestion des Commentaires et Evaluations
class ReviewRating(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',  # English related_name
        verbose_name=_("Product"), db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"), db_index=True
    )
    rating = models.IntegerField(
        _("Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_("Comment"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        verbose_name = _("Review & Rating")
        verbose_name_plural = _("Reviews & Ratings")

    def __str__(self):
        return f'Review by {self.user} for {self.product.name}: {self.rating} stars'

# Gestion des mentions legaux
class LegalContent(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name=_("Titre de la page")
    )
    # Ce slug correspondra aux IDs des liens dans le footer (ex: 'cond-gv', 'faq')
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_("Identifiant (slug)"),
        help_text=_("Identifiant unique utilisé pour lier le contenu au lien du footer. Doit correspondre à l'ID du lien HTML.")
    )
    # RichTextField permet d'utiliser un éditeur de texte avancé dans l'admin
    content = CKEditor5Field(
        verbose_name=_("Contenu de la page")
    )

    class Meta:
        verbose_name = _("Information Légale")
        verbose_name_plural = _("Informations Légales")

    def __str__(self):
        return self.title


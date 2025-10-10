from django.contrib import admin
from django.utils.text import slugify
from mptt.admin import DraggableMPTTAdmin
from .models import (
    Product, ProductImage, ProductFeature, Category, NewsLetter, Banner,
    BestSeller, Toast, Blog, Cta, Promotion, PromoCode, OrderItem, Order,
    CartItem, Cart, ReviewRating, LegalContent
)


# --- Inlines pour les produits (inchangé) ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1


# --- Modèles Admin personnalisés ---

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_price', 'stock', 'status', 'category')
    list_filter = ('status', 'category')
    search_fields = ('name', 'subname')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductFeatureInline]
    list_select_related = ('category',) # ✅ Bonus : optimise l'affichage de la catégorie

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(LegalContent)
class LegalContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

# ----------------------------------------------------------------
# ✅ NOUVELLE CLASSE ADMIN POUR OPTIMISER CartItem
# ----------------------------------------------------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cart', 'product', 'quantity')
    # Indique à Django de précharger le produit et le panier en une seule requête
    list_select_related = ('product', 'cart')

# ----------------------------------------------------------------
# ✅ NOUVELLE CLASSE ADMIN POUR OPTIMISER OrderItem
# ----------------------------------------------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'order', 'product', 'quantity', 'price')
    # Pré-charge la commande, le produit, et l'utilisateur lié à la commande
    list_select_related = ('order', 'product', 'order__user')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'status', 'paid', 'created_at')
    list_filter = ('status', 'paid', 'created_at')
    # Pré-charge l'utilisateur pour éviter une requête dans __str__
    list_select_related = ('user',)

@admin.register(ReviewRating)
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    # Pré-charge le produit et l'utilisateur
    list_select_related = ('product', 'user')


# --- Enregistrement des autres modèles (sans configuration spéciale) ---
@admin.register(NewsLetter)
class NewsLetterAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

admin.site.register(Banner)
admin.site.register(BestSeller)
admin.site.register(Toast)
admin.site.register(Blog)
admin.site.register(Cta)
admin.site.register(Promotion)
admin.site.register(Cart)


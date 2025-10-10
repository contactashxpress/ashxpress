from django.urls import path
from store import views


urlpatterns = [
    path('', views.index, name="index"),
    path('cart/', views.cart, name="cart"),
    path('api/session-data/', views.get_session_data, name='api_get_session_data'), # ✅ URL et nom mis à jour
    path('product/<str:slug>/add-to-cart', views.add_to_cart, name="add_to_cart"),
    path('product/<str:slug>/', views.detail, name="product"),
    path('decrement/<int:item_id>/', views.decrement, name="decrement"),
    path('cart/<int:item>/', views.delete_item, name="delete_item"),
    path('cart/emty_cart/', views.empty_cart, name="empty_cart"),
    #path('news_letter/', views.news_letter, name="news_letter"),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('cart/apply-promo/', views.apply_promo_code, name='apply_promo_code'),
    path('create/', views.create_order, name='create_order'),
    path('order/buy-now/<slug:slug>/', views.create_single_product_order, name='create_single_product_order'),
    path('cart/apply-promo/', views.apply_promo_code, name='apply_promo_code'),
    path('created/', views.order_created, name='order_created'),
    path('orders/history/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path("product/<slug:slug>/like/", views.toggle_like, name="toggle_like"),

    #Gestion de payement par cinetpay
    path('payment/notify/', views.cinetpay_notify, name='cinetpay_notify'),
    path('payment/return/', views.payment_return, name='payment_return'),
    path("product/<slug:slug>/like/", views.toggle_like, name="toggle_like"),

]


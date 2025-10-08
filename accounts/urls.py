from django.urls import path
from accounts import views

urlpatterns = [

# Gestion d'inscription, connexion et deconnexion (inchangé)
    path('inscription/', views.inscription, name="inscription"),
    path('connexion/', views.connexion, name="connexion"),
    path('deconnexion/', views.deconnexion, name="deconnexion"),

    # GESTION DE LA RÉINITIALISATION DU MOT DE PASSE (UTILISATEUR DÉCONNECTÉ)
    path('password-reset/',
         views.CustomPasswordResetView.as_view(),
         name="password_reset"),

    path('reset-password-sent/',
         views.CustomPasswordResetDoneView.as_view(),
         name="password_reset_done"),

    path('reset/<uidb64>/<token>/',
         views.CustomPasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),

    path('reset-password-complete/',
         views.CustomPasswordResetCompleteView.as_view(),
         name="password_reset_complete"),

    # GESTION DU CHANGEMENT DE MOT DE PASSE (UTILISATEUR CONNECTÉ)
    path('password-change/',
         views.CustomPasswordChangeView.as_view(),
         name="password_change"),

    path('password-change-done/',
         views.CustomPasswordChangeDoneView.as_view(),
         name="password_change_done"),
]
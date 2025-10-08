from axes.decorators import axes_dispatch
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from .emails import send_password_change_email, send_welcome_email
from django.contrib.auth import views as auth_views
from accounts.forms import InscriptionForm, ConnexionForm, CustomPasswordResetForm


# Gestion de l'inscription
def inscription(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()

            # On sauvegarde la clé de session de l'invité AVANT de le connecter
            guest_session_key = request.session.session_key
            if guest_session_key:
                request.session['guest_session_key'] = guest_session_key

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # Envoie d'email de bienvenu
            send_welcome_email(user.id)

            messages.success(request, _("Inscription réussie ! Bienvenue 👋"), extra_tags="inscription")
            return redirect('index')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."), extra_tags="inscription")
    else:
        form = InscriptionForm()
    return render(request, 'accounts/inscription.html', {"form": form})

# Gestion de la connexion
@axes_dispatch
def connexion(request):
    if request.user.is_authenticated:
        return redirect('index')

    next_url = request.GET.get('next', 'index')

    if request.method == "POST":
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # On sauvegarde la clé de session de l'invité AVANT de le connecter
            guest_session_key = request.session.session_key
            if guest_session_key:
                request.session['guest_session_key'] = guest_session_key

            login(request, user)

            # Gestion du "remember me"
            remember_me = bool(form.cleaned_data.get("remember_me", False))
            if remember_me:
                request.session.set_expiry(1209600)  # 2 semaines
            else:
                request.session.set_expiry(0)  # expire à la fermeture

            messages.success(request, _("Connexion réussie ✅"), extra_tags="connexion")

            if url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect('index')

        else:
            messages.error(request, _("Identifiants invalides."), extra_tags="connexion")
    else:
        form = ConnexionForm()  # Correction ici

    return render(request, 'accounts/connexion.html', {"form": form})

# Gestion de la deconnexion
@login_required
def deconnexion(request):
    logout(request)
    messages.info(request, _("Vous avez été déconnecté."), extra_tags="deconnexion")
    return redirect('index')



# GESTION DU CHANGEMENT DE MOT DE PASSE (UTILISATEUR CONNECTÉ)
class CustomPasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change_form.html'


class CustomPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            send_password_change_email(request.user.id)
        return super().dispatch(request, *args, **kwargs)


# GESTION DE LA RÉINITIALISATION DU MOT DE PASSE (UTILISATEUR NON CONNECTÉ)
class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

    # On définit les deux templates ici, et Django s'occupe du reste !
    email_template_name = 'registration/password_reset_email.html'        # Pour le texte brut
    html_email_template_name = 'registration/password_reset_html_email.html' # Pour le HTML


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'

    def form_valid(self, form):
        # Avant que le mot de passe ne soit changé, on récupère l'utilisateur
        user = form.user
        # Et on stocke son ID dans la session pour le retrouver à l'étape suivante
        self.request.session['password_reset_user_id'] = user.id
        return super().form_valid(form)


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

    def dispatch(self, request, *args, **kwargs):
        # On récupère l'ID de l'utilisateur depuis la session
        user_id = request.session.get('password_reset_user_id')
        if user_id:
            send_password_change_email(user_id)
            # On nettoie la session pour ne pas laisser traîner l'ID
            del request.session['password_reset_user_id']
        return super().dispatch(request, *args, **kwargs)


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordResetForm
from accounts.models import User

# FORMULAIRE D'INSCRIPTION
class InscriptionForm(UserCreationForm):
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom d'utilisateur")
        })
    )

    email = forms.EmailField(
        label=_("Adresse e-mail"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Adresse e-mail")
        })
    )

    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Mot de passe")
        })
    )

    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Confirmer le mot de passe")
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Cette adresse e-mail est déjà utilisée."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if " " in username:
            raise forms.ValidationError(_("Le nom d'utilisateur ne doit pas contenir d'espaces."))
        return username


# FORMULAIRE DE CONNEXION
class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        # On change le label et le placeholder pour être plus clair
        label=_("Nom d'utilisateur ou e-mail"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom d'utilisateur ou Email")
        })
    )

    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Mot de passe")
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        label=_("Se souvenir de moi"),
        widget=forms.CheckboxInput(attrs={
            'class': 'remember-me-checkbox',
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if " " in username:
            raise forms.ValidationError(_("Le nom d'utilisateur ne doit pas contenir d'espaces"))
        return username

# Gestion de modifications de mot de pass
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


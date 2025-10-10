from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order, ReviewRating


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'postal_code', 'city']
        labels = {
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
            'email': _('Email'),
            'phone': _('Téléphone'),
            'address': _('Adresse'),
            'postal_code': _('Code postal'),
            'city': _('Ville'),
        }
        help_texts = {
            'email': _('Veuillez entrer une adresse email valide.'),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': _('votre note de 1 à 5 étoiles'),
            'comment': _('votre commentaire'),
        }


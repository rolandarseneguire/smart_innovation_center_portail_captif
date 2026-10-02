import re
from django import forms
from django.core.validators import RegexValidator
from .models import Service, Enterprise


class RegistrationForm(forms.Form):
    nom = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Entrez votre nom'
        })
    )

    prenom = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Entrez votre prénom'
        })
    )

    numero = forms.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^(?:\+225)?\d{10}$',
                message="Entrez un numéro de téléphone valide (Ex: 0700000000 ou +2250700000000)."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ex: 0700000000',
            'type': 'tel'
        })
    )

    pole_service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        empty_label="-- Sélectionner un service (Optionnel) --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    enterprise = forms.ModelChoiceField(
        queryset=Enterprise.objects.all(),
        required=False,
        empty_label="-- Sélectionner une entreprise (Optionnel) --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_numero(self):
        numero = self.cleaned_data.get('numero', '').strip()
        numero = re.sub(r'[\s\-\(\)]', '', numero)
        return numero
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Game, Profile


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            "genre",
            "slug",
            "title",
            "description",
            "platform",
            "price",
            "stock",
            "availability",
            "cover",
            "is_active",
        ]
        widgets = {
            "genre": forms.Select(attrs={"class": "form-select"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "platform": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "availability": forms.Select(attrs={"class": "form-select"}),
            "cover": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug", ""))
        if not slug:
            raise ValidationError("Ingresa un código con letras o números.")
        qs = Game.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un videojuego con este código.")
        return slug

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("El precio no puede ser negativo.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is not None and stock < 0:
            raise ValidationError("Las unidades disponibles no pueden ser negativas.")
        return stock


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    rut = forms.CharField(
        label="RUT",
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(
                user=user,
                rut=self.cleaned_data["rut"],
                phone=self.cleaned_data["phone"],
            )
        return user


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=999)

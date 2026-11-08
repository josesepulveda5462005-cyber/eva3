import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField("nombre", max_length=80, unique=True)
    slug = models.SlugField("identificador", max_length=90, unique=True)
    description = models.TextField("descripción", blank=True)
    is_active = models.BooleanField("vigente", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "género"
        verbose_name_plural = "géneros"

    def __str__(self):
        return self.name


class Game(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        PREORDER = "preorder", "Preventa"
        UNAVAILABLE = "unavailable", "Agotado"

    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        related_name="games",
        verbose_name="género",
    )
    slug = models.SlugField(
        "código",
        max_length=100,
        unique=True,
        help_text="Identificador único usado también en la dirección del videojuego.",
    )
    title = models.CharField("título", max_length=140)
    description = models.TextField("descripción")
    platform = models.CharField("plataforma", max_length=60)
    price = models.DecimalField(
        "precio (CLP)",
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(
        "unidades disponibles",
        default=0,
        validators=[MinValueValidator(0)],
    )
    availability = models.CharField(
        "estado",
        max_length=12,
        choices=Availability.choices,
        default=Availability.AVAILABLE,
    )
    cover = models.ImageField(
        "portada",
        upload_to="game_covers/",
        blank=True,
    )
    is_active = models.BooleanField("vigente", default=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "videojuego"
        verbose_name_plural = "videojuegos"

    def __str__(self):
        return self.title

    @property
    def is_purchasable(self):
        return (
            self.is_active
            and self.availability == self.Availability.AVAILABLE
            and self.stock > 0
        )


class Profile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Cliente"
        STAFF = "staff", "Personal"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    rut = models.CharField("RUT", max_length=12, blank=True)
    phone = models.CharField("teléfono", max_length=30, blank=True)
    role = models.CharField(
        "rol institucional",
        max_length=12,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self):
        return f"Perfil de {self.user.username}"


class OrderRequest(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Solicitud confirmada"

    code = models.UUIDField("comprobante", default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="order_requests",
        verbose_name="cliente",
    )
    status = models.CharField(
        "estado",
        max_length=12,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    total = models.DecimalField(
        "total (CLP)",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField("fecha de solicitud", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitud de compra"
        verbose_name_plural = "solicitudes de compra"

    def __str__(self):
        return f"Solicitud {self.code}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        OrderRequest,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="solicitud",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="videojuego",
    )
    title_snapshot = models.CharField("título al comprar", max_length=140)
    unit_price = models.DecimalField("precio unitario (CLP)", max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField("cantidad")

    class Meta:
        ordering = ["title_snapshot"]
        verbose_name = "detalle de solicitud"
        verbose_name_plural = "detalles de solicitud"
        constraints = [
            models.UniqueConstraint(fields=["order", "game"], name="unique_game_per_order")
        ]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

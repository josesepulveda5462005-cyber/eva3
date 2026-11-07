from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .management.commands.poblar_datos import GAMES
from .models import Game, Genre, OrderItem, OrderRequest, Profile


class StoreWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.genre = Genre.objects.create(name="Aventura", slug="aventura")
        cls.game = Game.objects.create(
            genre=cls.genre,
            slug="nebula-run",
            title="Nebula Run",
            description="Explora el espacio.",
            platform="PC",
            price=Decimal("12990"),
            stock=3,
        )
        cls.customer = User.objects.create_user(username="cliente", password="StrongPass123!")
        Profile.objects.create(user=cls.customer)
        cls.staff = User.objects.create_user(
            username="staff",
            password="StrongPass123!",
            is_staff=True,
        )

    def test_catalog_supports_search_and_genre_filters(self):
        response = self.client.get(reverse("catalog"), {"q": "Nebula", "genre": "aventura"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nebula Run")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_add_and_update_session_cart_calculates_total_from_database(self):
        response = self.client.post(
            reverse("cart_add", args=[self.game.pk]),
            {"quantity": 2},
        )
        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(self.client.session["cart"], {str(self.game.pk): 2})

        response = self.client.get(reverse("cart"))
        self.assertContains(response, "CLP $25980")
        self.assertTrue(response.context["can_checkout"])

        self.client.post(
            reverse("cart_update", args=[self.game.pk]),
            {"quantity": 3},
        )
        self.assertEqual(self.client.session["cart"], {str(self.game.pk): 3})

    def test_cart_rejects_quantity_above_stock(self):
        self.client.post(
            reverse("cart_add", args=[self.game.pk]),
            {"quantity": 4},
        )
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_cart_supports_individual_removal_and_emptying(self):
        self.client.post(reverse("cart_add", args=[self.game.pk]), {"quantity": 1})
        self.client.post(reverse("cart_remove", args=[self.game.pk]))
        self.assertEqual(self.client.session["cart"], {})

        self.client.post(reverse("cart_add", args=[self.game.pk]), {"quantity": 1})
        self.client.post(reverse("cart_clear"))
        self.assertNotIn("cart", self.client.session)

    def test_checkout_persists_receipt_decrements_stock_and_clears_session(self):
        self.client.force_login(self.customer)
        session = self.client.session
        session["cart"] = {str(self.game.pk): 2}
        session.save()

        response = self.client.post(reverse("checkout"))
        order = OrderRequest.objects.get(user=self.customer)
        self.assertRedirects(response, reverse("order_detail", args=[order.code]))
        self.assertEqual(order.total, Decimal("25980"))
        self.assertEqual(
            OrderItem.objects.get(order=order).unit_price,
            Decimal("12990"),
        )
        self.game.refresh_from_db()
        self.assertEqual(self.game.stock, 1)
        self.assertNotIn("cart", self.client.session)

    def test_checkout_requires_login(self):
        session = self.client.session
        session["cart"] = {str(self.game.pk): 1}
        session.save()
        response = self.client.post(reverse("checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertFalse(OrderRequest.objects.exists())

    def test_management_crud_is_staff_only_and_deactivate_is_logical(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("management_games"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.staff)
        response = self.client.get(reverse("game_deactivate", args=[self.game.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("game_deactivate", args=[self.game.pk]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.game.refresh_from_db()
        self.assertFalse(self.game.is_active)
        self.assertTrue(Game.objects.filter(pk=self.game.pk).exists())

    def test_staff_can_create_and_update_games(self):
        self.client.force_login(self.staff)
        game_data = {
            "genre": self.genre.pk,
            "slug": "new-game",
            "title": "New Game",
            "description": "Un nuevo mundo.",
            "platform": "PC",
            "price": "900",
            "stock": "2",
            "availability": Game.Availability.AVAILABLE,
            "is_active": "on",
        }
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="white").save(image_buffer, format="PNG")
        game_data["cover"] = SimpleUploadedFile(
            "cover.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(reverse("game_create"), game_data)
            self.assertRedirects(response, reverse("management_games"))
            game = Game.objects.get(slug="new-game")
            self.assertTrue(Path(game.cover.path).is_file())

            game_data["title"] = "Updated Game"
            game_data["price"] = "1200"
            game_data.pop("cover")
            response = self.client.post(
                reverse("game_update", args=[game.pk]),
                game_data,
            )
            self.assertRedirects(response, reverse("management_games"))
            game.refresh_from_db()
            self.assertEqual(game.title, "Updated Game")
            self.assertEqual(game.price, Decimal("1200"))

    def test_registration_creates_customer_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "nueva",
                "first_name": "Nueva",
                "last_name": "Persona",
                "email": "nueva@example.com",
                "rut": "12.345.678-9",
                "phone": "+56912345678",
                "password1": "UnicaClave2026!",
                "password2": "UnicaClave2026!",
            },
        )
        self.assertRedirects(response, reverse("catalog"))
        profile = Profile.objects.get(user__username="nueva")
        self.assertEqual(profile.rut, "12.345.678-9")
        self.assertEqual(profile.role, Profile.Role.CUSTOMER)

    def test_seed_command_loads_real_games_and_retires_legacy_samples(self):
        call_command("poblar_datos", stdout=StringIO())

        self.assertEqual(
            Game.objects.filter(slug__in=[game[0] for game in GAMES], is_active=True).count(),
            len(GAMES),
        )
        self.assertFalse(Game.objects.get(slug="nebula-run").is_active)
        self.assertTrue(
            Game.objects.filter(
                slug="grand-theft-auto-san-andreas",
                title="Grand Theft Auto: San Andreas",
                is_active=True,
            ).exists()
        )
        response = self.client.get(reverse("catalog"), {"q": "Grand Theft Auto"})
        self.assertContains(response, "Grand Theft Auto: San Andreas")
        self.assertContains(response, "game-cover--grand-theft-auto-san-andreas")

        covers_dir = Path(__file__).parent / "static" / "store" / "img" / "covers"
        for slug, *_ in GAMES:
            cover_path = covers_dir / f"{slug}.png"
            self.assertTrue(cover_path.is_file(), f"Falta la ilustración de {slug}")
            with Image.open(cover_path) as cover:
                cover.verify()

        self.assertContains(
            response,
            "/static/store/img/covers/grand-theft-auto-san-andreas.png",
        )
        response = self.client.get(
            reverse("game_detail", args=["grand-theft-auto-san-andreas"])
        )
        self.assertContains(
            response,
            "/static/store/img/covers/grand-theft-auto-san-andreas.png",
        )
        self.assertNotContains(response, "cover-title")

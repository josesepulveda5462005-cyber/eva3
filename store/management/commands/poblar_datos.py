import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from store.models import Game, Genre, Profile


GENRES = [
    ("Aventura", "aventura", "Historias y mundos por descubrir."),
    ("Estrategia", "estrategia", "Planificación, táctica y decisiones."),
    ("Acción", "accion", "Combate y desafíos de ritmo intenso."),
    ("Simulación", "simulacion", "Experiencias para construir y experimentar."),
]

GAMES = [
    ("assassins-creed-unity", "Assassin's Creed Unity", "Aventura", "PC", 24990, 8, "Explora una recreación de París durante la Revolución francesa en esta aventura de acción histórica."),
    ("assassins-creed-ii", "Assassin's Creed II", "Aventura", "PC", 14990, 10, "Acompaña a Ezio Auditore en una aventura de acción ambientada en la Italia del Renacimiento."),
    ("grand-theft-auto-san-andreas", "Grand Theft Auto: San Andreas", "Acción", "PC", 12990, 12, "Recorre el estado ficticio de San Andreas en una aventura de mundo abierto."),
    ("grand-theft-auto-v", "Grand Theft Auto V", "Acción", "PC", 19990, 7, "Explora Los Santos y su condado en una aventura de acción de mundo abierto."),
    ("red-dead-redemption-2", "Red Dead Redemption 2", "Aventura", "PC", 29990, 5, "Vive una aventura de acción en un mundo abierto inspirado en el oeste estadounidense."),
    ("the-witcher-3-wild-hunt", "The Witcher 3: Wild Hunt", "Aventura", "PC", 24990, 6, "Explora un mundo de fantasía y sigue una aventura de rol como Geralt de Rivia."),
    ("cyberpunk-2077", "Cyberpunk 2077", "Acción", "PC", 24990, 6, "Descubre Night City en un juego de rol y acción ambientado en un futuro distópico."),
    ("minecraft", "Minecraft", "Simulación", "PC", 22990, 15, "Explora, construye y crea en un mundo abierto compuesto por bloques."),
    ("elden-ring", "Elden Ring", "Aventura", "PC", 34990, 4, "Explora las Tierras Intermedias en un juego de rol de acción y fantasía."),
    ("age-of-empires-ii-definitive-edition", "Age of Empires II: Definitive Edition", "Estrategia", "PC", 15990, 9, "Desarrolla una civilización y compite en partidas de estrategia en tiempo real."),
    ("stardew-valley", "Stardew Valley", "Simulación", "PC", 8990, 20, "Administra una granja y construye una vida en un pueblo rural."),
    ("forza-horizon-5", "Forza Horizon 5", "Simulación", "PC / Xbox", 29990, 5, "Conduce en un festival de automovilismo ambientado en distintas regiones de México."),
]

LEGACY_SAMPLE_SLUGS = (
    "nebula-run",
    "atlas-de-ceniza",
    "isla-de-circuitos",
    "reinos-del-norte",
    "ferro-y-humo",
    "bruma-carmesi",
    "jardin-de-titanes",
    "ruta-del-cometa",
)


class Command(BaseCommand):
    help = "Carga videojuegos reales para una tienda de demostración de Ludix."

    def handle(self, *args, **options):
        genres = {}
        for name, slug, description in GENRES:
            genre, _ = Genre.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "description": description, "is_active": True},
            )
            genres[name] = genre

        Game.objects.filter(slug__in=LEGACY_SAMPLE_SLUGS).update(is_active=False)

        for slug, title, genre_name, platform, price, stock, description in GAMES:
            Game.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "genre": genres[genre_name],
                    "description": description,
                    "platform": platform,
                    "price": price,
                    "stock": stock,
                    "availability": Game.Availability.AVAILABLE,
                    "is_active": True,
                },
            )

        self._create_demo_user(
            username="admin",
            password=os.getenv("LUDIX_ADMIN_PASSWORD", "AdminLudix2026!"),
            email="admin@ludix.local",
            is_staff=True,
            is_superuser=True,
            role=Profile.Role.STAFF,
        )
        self._create_demo_user(
            username="jugador",
            password="JugadorLudix2026!",
            email="jugador@ludix.local",
            is_staff=False,
            is_superuser=False,
            role=Profile.Role.CUSTOMER,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Datos listos: {len(GENRES)} géneros, {len(GAMES)} videojuegos y usuarios de prueba."
            )
        )

    def _create_demo_user(self, username, password, email, is_staff, is_superuser, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        Profile.objects.update_or_create(user=user, defaults={"role": role})

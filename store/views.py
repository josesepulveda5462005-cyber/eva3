from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CartQuantityForm, GameForm, RegistrationForm
from .models import Game, Genre, OrderItem, OrderRequest


def is_staff(user):
    return user.is_staff


def _session_cart(request):
    stored = request.session.get("cart", {})
    if not isinstance(stored, dict):
        return {}
    cart = {}
    for game_id, quantity in stored.items():
        try:
            game_id = str(int(game_id))
        except (TypeError, ValueError):
            continue
        if isinstance(quantity, int) and not isinstance(quantity, bool) and quantity > 0:
            cart[game_id] = quantity
    return cart


def catalog(request):
    games = Game.objects.filter(is_active=True).select_related("genre")
    genres = Genre.objects.filter(is_active=True)
    query = request.GET.get("q", "").strip()
    genre_slug = request.GET.get("genre", "").strip()
    ordering = request.GET.get("order", "title")

    if query:
        games = games.filter(
            Q(title__icontains=query)
            | Q(slug__icontains=query)
            | Q(description__icontains=query)
            | Q(platform__icontains=query)
            | Q(genre__name__icontains=query)
        )
    if genre_slug:
        games = games.filter(genre__slug=genre_slug, genre__is_active=True)

    orderings = {
        "title": "title",
        "price_asc": "price",
        "price_desc": "-price",
        "newest": "-created_at",
    }
    if ordering not in orderings:
        ordering = "title"
    games = games.order_by(orderings[ordering])

    page_obj = Paginator(games, 9).get_page(request.GET.get("page"))
    return render(
        request,
        "store/catalog.html",
        {
            "page_obj": page_obj,
            "games": page_obj.object_list,
            "genres": genres,
            "query": query,
            "selected_genre": genre_slug,
            "selected_order": ordering,
        },
    )


def game_detail(request, slug):
    game = get_object_or_404(
        Game.objects.select_related("genre"),
        slug=slug,
        is_active=True,
    )
    return render(request, "store/game_detail.html", {"game": game})


def register(request):
    if request.user.is_authenticated:
        return redirect("catalog")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tu cuenta Ludix está lista.")
        return redirect("catalog")
    return render(request, "registration/register.html", {"form": form})


def cart(request):
    stored_cart = _session_cart(request)
    if stored_cart != request.session.get("cart", {}):
        request.session["cart"] = stored_cart
    games = Game.objects.filter(pk__in=stored_cart.keys()).select_related("genre")
    game_map = {str(game.pk): game for game in games}
    lines = []
    total = Decimal("0")
    for game_id, quantity in stored_cart.items():
        game = game_map.get(game_id)
        if game is None:
            continue
        line_total = game.price * quantity
        total += line_total
        lines.append(
            {
                "game": game,
                "quantity": quantity,
                "line_total": line_total,
                "available": game.is_purchasable and game.stock >= quantity,
            }
        )
    return render(
        request,
        "store/cart.html",
        {
            "lines": lines,
            "total": total,
            "can_checkout": bool(lines) and all(line["available"] for line in lines),
        },
    )


@require_POST
def cart_add(request, game_id):
    game = get_object_or_404(Game, pk=game_id, is_active=True)
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Ingresa una cantidad válida.")
        return redirect("game_detail", slug=game.slug)

    if not game.is_purchasable:
        messages.warning(request, "Este videojuego no está disponible por ahora.")
        return redirect("game_detail", slug=game.slug)

    cart_items = _session_cart(request)
    new_quantity = cart_items.get(str(game.pk), 0) + form.cleaned_data["quantity"]
    if new_quantity > game.stock:
        messages.warning(request, f"Solo quedan {game.stock} unidades disponibles.")
        return redirect("game_detail", slug=game.slug)

    cart_items[str(game.pk)] = new_quantity
    request.session["cart"] = cart_items
    messages.success(request, f"{game.title} se agregó a tu carrito.")
    return redirect("cart")


@require_POST
def cart_update(request, game_id):
    cart_items = _session_cart(request)
    game_key = str(game_id)
    if game_key not in cart_items:
        messages.error(request, "Ese videojuego ya no está en tu carrito.")
        return redirect("cart")

    form = CartQuantityForm(request.POST)
    game = get_object_or_404(Game, pk=game_id)
    if not form.is_valid():
        messages.error(request, "Ingresa una cantidad válida.")
    elif not game.is_purchasable or form.cleaned_data["quantity"] > game.stock:
        messages.warning(request, f"La cantidad supera el stock disponible ({game.stock}).")
    else:
        cart_items[game_key] = form.cleaned_data["quantity"]
        request.session["cart"] = cart_items
        messages.success(request, "Cantidad actualizada.")
    return redirect("cart")


@require_POST
def cart_remove(request, game_id):
    cart_items = _session_cart(request)
    cart_items.pop(str(game_id), None)
    request.session["cart"] = cart_items
    messages.info(request, "Videojuego eliminado del carrito.")
    return redirect("cart")


@require_POST
def cart_clear(request):
    request.session.pop("cart", None)
    messages.info(request, "Vaciaste tu carrito.")
    return redirect("cart")


@login_required
@require_POST
def checkout(request):
    cart_items = _session_cart(request)
    if not cart_items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    quantities = {int(game_id): quantity for game_id, quantity in cart_items.items()}
    with transaction.atomic():
        games = list(
            Game.objects.select_for_update()
            .filter(pk__in=quantities)
            .order_by("pk")
        )
        if len(games) != len(quantities):
            messages.error(request, "Un videojuego del carrito ya no está disponible.")
            return redirect("cart")
        if any(
            not game.is_purchasable or game.stock < quantities[game.pk]
            for game in games
        ):
            messages.error(request, "El stock cambió. Revisa las cantidades de tu carrito.")
            return redirect("cart")

        total = sum(
            (game.price * quantities[game.pk] for game in games),
            Decimal("0"),
        )
        order = OrderRequest.objects.create(user=request.user, total=total)
        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    game=game,
                    title_snapshot=game.title,
                    unit_price=game.price,
                    quantity=quantities[game.pk],
                )
                for game in games
            ]
        )
        for game in games:
            game.stock -= quantities[game.pk]
            if game.stock == 0:
                game.availability = Game.Availability.UNAVAILABLE
            game.save(update_fields=["stock", "availability", "updated_at"])

    request.session.pop("cart", None)
    messages.success(request, "Solicitud confirmada. Este comprobante es una simulación.")
    return redirect("order_detail", code=order.code)


@login_required
def order_history(request):
    orders = OrderRequest.objects.filter(user=request.user)
    return render(request, "store/order_history.html", {"orders": orders})


@login_required
def order_detail(request, code):
    order = get_object_or_404(
        OrderRequest.objects.prefetch_related("items"),
        code=code,
        user=request.user,
    )
    return render(request, "store/order_detail.html", {"order": order})


@login_required
@user_passes_test(is_staff, login_url="login")
def management_games(request):
    games = Game.objects.select_related("genre").all()
    return render(request, "store/manage_games.html", {"games": games})


@login_required
@user_passes_test(is_staff, login_url="login")
def game_create(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        game = form.save()
        messages.success(request, f"Se creó {game.title}.")
        return redirect("management_games")
    return render(
        request,
        "store/game_form.html",
        {"form": form, "page_title": "Agregar videojuego"},
    )


@login_required
@user_passes_test(is_staff, login_url="login")
def game_update(request, pk):
    game = get_object_or_404(Game, pk=pk)
    form = GameForm(request.POST or None, request.FILES or None, instance=game)
    if request.method == "POST" and form.is_valid():
        game = form.save()
        messages.success(request, f"Se actualizaron los datos de {game.title}.")
        return redirect("management_games")
    return render(
        request,
        "store/game_form.html",
        {"form": form, "page_title": "Editar videojuego", "game": game},
    )


@login_required
@user_passes_test(is_staff, login_url="login")
def game_deactivate(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        game.is_active = False
        game.availability = Game.Availability.UNAVAILABLE
        game.save(update_fields=["is_active", "availability", "updated_at"])
        messages.success(request, f"{game.title} quedó fuera del catálogo.")
        return redirect("management_games")
    return render(request, "store/game_confirm_deactivate.html", {"game": game})

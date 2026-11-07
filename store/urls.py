from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("juego/<slug:slug>/", views.game_detail, name="game_detail"),
    path("cuenta/registro/", views.register, name="register"),
    path(
        "cuenta/ingresar/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("cuenta/salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("cuenta/solicitudes/", views.order_history, name="order_history"),
    path("cuenta/solicitudes/<uuid:code>/", views.order_detail, name="order_detail"),
    path("carrito/", views.cart, name="cart"),
    path("carrito/agregar/<int:game_id>/", views.cart_add, name="cart_add"),
    path("carrito/actualizar/<int:game_id>/", views.cart_update, name="cart_update"),
    path("carrito/quitar/<int:game_id>/", views.cart_remove, name="cart_remove"),
    path("carrito/vaciar/", views.cart_clear, name="cart_clear"),
    path("carrito/confirmar/", views.checkout, name="checkout"),
    path("gestion/videojuegos/", views.management_games, name="management_games"),
    path("gestion/videojuegos/nuevo/", views.game_create, name="game_create"),
    path("gestion/videojuegos/<int:pk>/editar/", views.game_update, name="game_update"),
    path(
        "gestion/videojuegos/<int:pk>/desactivar/",
        views.game_deactivate,
        name="game_deactivate",
    ),
]

from django.contrib import admin

from .models import Game, Genre, OrderItem, OrderRequest, Profile

admin.site.site_header = "Ludix - Panel de Control"
admin.site.site_title = "Ludix Admin"
admin.site.index_title = "Gestión Operativa de Recursos y Servicios"


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    list_editable = ("is_active",)
    fieldsets = (
        ("Identificación", {"fields": ("name", "slug")}),
        ("Descripción", {"fields": ("description",)}),
        ("Vigencia", {"fields": ("is_active",)}),
    )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "genre", "price", "availability", "is_active")
    list_filter = ("genre", "availability", "is_active", "platform")
    search_fields = ("slug", "title", "description", "platform")
    list_editable = ("price", "availability", "is_active")
    list_select_related = ("genre",)
    fieldsets = (
        ("Identificación", {"fields": ("slug", "title", "genre", "platform")}),
        ("Descripción y portada", {"fields": ("description", "cover")}),
        ("Precio y disponibilidad", {"fields": ("price", "stock", "availability")}),
        ("Vigencia", {"fields": ("is_active",)}),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("game", "title_snapshot", "unit_price", "quantity")


@admin.register(OrderRequest)
class OrderRequestAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("code", "user__username", "user__email")
    readonly_fields = ("code", "user", "status", "total", "created_at")
    inlines = (OrderItemInline,)

    def has_add_permission(self, request):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rut", "phone", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "rut")

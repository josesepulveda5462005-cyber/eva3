from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def game_cover_url(game):
    if game.cover:
        return game.cover.url

    image_path = f"store/img/covers/{game.slug}.png"
    if finders.find(image_path):
        return static(image_path)

    return ""

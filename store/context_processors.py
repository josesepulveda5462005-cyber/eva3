def cart_summary(request):
    cart = request.session.get("cart", {})
    count = sum(
        quantity
        for quantity in cart.values()
        if isinstance(quantity, int) and quantity > 0
    )
    return {"cart_count": count}

from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

    cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

    if cart_item_qs.exists():
        existing_variations_list = [list(item.variations.all()) for item in cart_item_qs]
        if product_variation in existing_variations_list:
            index = existing_variations_list.index(product_variation)
            cart_item = cart_item_qs[index]
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variation:
                cart_item.variations.add(*product_variation)
            cart_item.save()
    else:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        if product_variation:
            cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    try:
        cart_item_qs = CartItem.objects.filter(product=product, cart=cart, id=cart_item_id)

        if cart_item_qs.exists():
            cart_item = cart_item_qs.first()
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    except CartItem.DoesNotExist:
        # Handle the case where the cart item doesn't exist
        pass
    except Exception as e:
        # Log or handle unexpected errors
        print(f"An error occurred: {e}")

    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    cart = get_object_or_404(Cart, cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    cart_item_qs = CartItem.objects.filter(product=product, cart=cart, id=cart_item_id)

    if cart_item_qs.exists():
        cart_item_qs.delete()

    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = get_object_or_404(Cart, cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

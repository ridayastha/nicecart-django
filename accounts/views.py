from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,

            )
            user.phone_number = phone_number
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Registration successful. Please check your email to activate your account.')

            return redirect(f"{reverse('login')}?command=verification&email={email}")
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)

                if cart_items.exists():
                    # Getting the product variations from the cart
                    product_variations = [list(item.variations.all()) for item in cart_items]

                    # Get the cart items for the logged-in user
                    user_cart_items = CartItem.objects.filter(user=user)
                    ex_var_list = [list(item.variations.all()) for item in user_cart_items]
                    id_list = [item.id for item in user_cart_items]

                    # Merge the cart items
                    for pr in product_variations:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id_list[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            # Assign user to items from guest cart
                            for item in cart_items:
                                item.user = user
                                item.save()

            except Cart.DoesNotExist:
                pass  # If the cart does not exist, continue

            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # Create UserProfile if it doesn't exist
        if not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(user=user)

        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')

@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    userprofile = UserProfile.objects.filter(user=request.user).first()  # Use first() to handle missing profiles

    context = {
      'orders_count': orders_count,
      'userprofile': userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has expired!')
        return redirect('login')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
       'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)

# @login_required(login_url='login')
# def edit_profile(request):
#     userprofile = get_object_or_404(UserProfile, user=request.user)

#     if request.method == 'POST':
#         user_form = UserForm(request.POST, instance=request.user)
#         profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

#         # Ensure both forms are valid before accessing cleaned_data
#         if user_form.is_valid() and profile_form.is_valid():
#             # Check if the profile picture should be cleared
#             if profile_form.cleaned_data.get('clear_profile_picture'):
#                 userprofile.profile_picture = None  # Clear profile picture
#                 userprofile.save()

#             # Save the forms
#             user_form.save()
#             profile_form.save()

#             messages.success(request, 'Your profile has been updated.')
#             return redirect('edit_profile')

#     else:
#         user_form = UserForm(instance=request.user)
#         profile_form = UserProfileForm(instance=userprofile)

#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'userprofile': userprofile,
#     }

#     return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    # Try to get the user's profile or create it if it doesn't exist
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        # Ensure both forms are valid before accessing cleaned_data
        if user_form.is_valid() and profile_form.is_valid():
            # Check if the profile picture should be cleared
            if profile_form.cleaned_data.get('clear_profile_picture'):
                userprofile.profile_picture = None  # Clear profile picture
                userprofile.save()

            # Save the forms
            user_form.save()
            profile_form.save()

            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/edit_profile.html', context)



@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter a valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Passwords do not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
      'order_detail': order_detail,
      'order': order,
      'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)

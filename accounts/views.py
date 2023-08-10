from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate , login , logout 
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from .models import Profile , Cart , CartItems
from products.models import *
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
import razorpay
from django.conf import settings



# Create your views here.
def login_page(request):

    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')

        user_obj = User.objects.filter(username=email)

        if not user_obj.exists():
            messages.warning(request, "Account not found.")
            return HttpResponseRedirect(request.path_info)
        
        if not user_obj[0].profile.is_email_verified:

            messages.warning(request, "Your account is not verified.")
            return HttpResponseRedirect(request.path_info)
        
        user_obj = authenticate(username= email , password= password)
        print(email, password)
        if user_obj:
            login(request, user_obj)
            return redirect('/')
        

        messages.warning(request, 'Invalid credentials')
        return HttpResponseRedirect(request.path_info)
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('/accounts/login')


def register_page(request):
    if request.method=='POST':
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email')
        password=request.POST.get('password')

        user_obj = User.objects.filter(username=email)

        if user_obj.exists():
            messages.warning(request, "Email is already taken.")
            return HttpResponseRedirect(request.path_info)
        

        user_obj=User.objects.create(first_name=first_name, last_name=last_name, email=email, username=email)
        user_obj.set_password(password)
        user_obj.save()
        messages.success(request, 'An email has been sent on your mail.')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')

def activate_email(request , email_token):
    try:
        user = Profile.objects.get(email_token= email_token)
        user.is_email_verified=True
        user.save()
        return redirect('/')
    
    except Exception as e:
        return HttpResponse('Invalid Email token')
    

def add_to_cart(request , uid):
    
    variant = request.GET.get('variant')
    product = Product.objects.get(uid = uid)
    user =request.user
    cart , _ = Cart.objects.get_or_create(user = user , is_paid = False)
    cart_item = CartItems.objects.create(cart = cart , product = product , )

    

    if variant:
        variant = request.GET.get('variant')
        size_variant = SizeVariant.objects.get(size_name= variant)
        cart_item.size_variant = size_variant
        cart_item.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def remove_cart(request , cart_item_uid):
    try:
        cart_item = CartItems.objects.get(uid = cart_item_uid)
        cart_item.delete()
    except Exception as e:
        print(e)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def cart(request):
        cart = None
        #User_mode=Profile.objects.get(user_id=uid).uid
        #cart_id=Cart.objects.get(user_id=uid).uid    
        #cart_items=CartItems.objects.filter(cart_id=cart_id)
        try:
            uid=request.user.id  
            cart = Cart.objects.get(user_id=uid , is_paid = False)
        except Exception as e:
            print(e)

        #total_price = cart.get_cart_total()
        #coupon_code ="" 
        #if cart.coupon:
        #    coupon_code=cart.coupon.coupn_code
        #context = {"cart" : Cart.objects.filter(is_paid=False, user= request.user)}
        context = {"cart" : cart}
        #context = {'cart_items':cart_items}  
        #context['total'] = total_price
        #context['coupon_code']=coupon_code
        #context['cart'] = cart
        if request.method =='POST':
              
              coupon = request.POST.get('coupon')
              coupon_obj = Coupon.objects.filter(coupn_code__icontains = coupon)
              if not coupon_obj.exists():
                  messages.warning(request, "Invalid Coupon.")
                  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
              if cart.coupon:
                  messages.warning(request, 'Coupon already exists.')
                  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
              
              if cart.get_cart_total() < coupon_obj[0].minimum_amount:
                  messages.warning(request, f'Amount should be greater than{coupon_obj[0].minimum_amount}.')
                  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
              
              if coupon_obj[0].is_expired:
                  messages.warning(request, 'Coupon expired.')
                  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
              cart.coupon = coupon_obj[0]
              cart.save()
              messages.success(request, 'Coupon applied.')
              return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        if cart:
            try:

                client = razorpay.Client(auth=(settings.KEY , settings.SECRET) )
                payment = client.order.create({ 'amount' : cart.get_cart_total()*100 , 'currency': 'INR' , 'payment_capture': 1 } )
                cart.razor_pay_order_id = payment['id']
                cart.save()
                print('***')
                print(payment)
                print('***')
                context['payment'] = payment
            except Exception as e:
                print(e)

        return render(request , 'accounts/cart.html' , context = context)

def remove_coupon(request , cart_id):
    cart = Cart.objects.get(uid = cart_id)
    cart.coupon = None
    cart.save()
    messages.success(request, 'Coupon reomved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def success(request):
    order_id = request.GET.get('order_id')
    print(order_id)
    cart = Cart.objects.get(razor_pay_order_id = order_id)
    cart.is_paid = True
    cart.save()
    return HttpResponse('Payment Success')

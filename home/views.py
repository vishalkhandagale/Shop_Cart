from django.shortcuts import render
from products.models import Product

# Create your views here.


def index(request):
    contex = {'products': Product.objects.all()}
    return render(request , 'home/index.html', contex)
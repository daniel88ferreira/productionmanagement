from django.views.generic import CreateView
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse

from .models import *

def index(request):
    return render(request, 'pm/index.html')

def orders(request):
    return HttpResponse("Here goes Production orders table.")

def products(request):
    return render(request, 'pm/products.html')

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print(request.POST)
            product = form.save(commit=False)
            form.save()
            return HttpResponseRedirect(reverse('pm:add_components', args=(product.id,)))
    else:
        form = ProductForm()

    return render(request, 'pm/add_product.html', {'form': form})


def add_components(request, productid):
    product = get_object_or_404(Product, pk=productid)
    if request.method == 'POST':
        form = QuantityForm(request.POST)
        if form.is_valid():
            print(request.POST)
            component = form.save(commit=False)
            component.product = product
            component.save()
            return HttpResponseRedirect(reverse('pm:products'))
    else:
        form = QuantityForm()

    return render(request, 'pm/add_components.html', {'form': form, 'productid': productid})



def product_detail(request, product_id):
    return HttpResponse("form to view and modify.")

def inventory(request):
    return HttpResponse("Here goes the stocks management.")
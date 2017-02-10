from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DetailView
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse

from .models import *

def index(request):
    return render(request, 'pm/index.html')

@login_required
def orders(request):
    return HttpResponse("Here goes Production orders table.")

@login_required
def products(request):
    all_products_list = Product.objects.order_by('ref_code')
    context = {
        'all_products_list': all_products_list,
    }
    return render(request, 'pm/products.html', context )


@login_required
def create_product(request):
    if request.method == 'POST':
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('pm:products'))
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            form.save()
            return HttpResponseRedirect(reverse('pm:add_components', args=(product.id,)))
    else:
        form = ProductForm()
    return render(request, 'pm/create_product.html', {'form': form})

@login_required
def add_components(request, productid):
    product = get_object_or_404(Product, pk=productid)
    components_list = None
    if request.method == 'POST':
        form = QuantityForm(request.POST)
        if "done" in request.POST:
            return HttpResponseRedirect(reverse('pm:product_detail', args=(product.id,)))
        if form.is_valid():
            component = form.save(commit=False)
            component.product = product
            component.save()
            return HttpResponseRedirect(reverse('pm:add_components', args=(product.id,)))
    else:
        form = QuantityForm()
    return render(request, 'pm/add_components.html', {'form': form, 'product': product})

class ProductDetail(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'pm/product_detail.html'

class ModifyProduct(UpdateView):
    model = Product
    fields = ['ref_code', 'name', 'color', 'size', 'components']
    template_name = 'pm/modify_product.html'

@login_required
def product_detail(request, product_id):
    return HttpResponse("form to view and modify.")

@login_required
def inventory(request):
    return HttpResponse("Here goes the stocks management.")
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DetailView
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse

from .forms import *
from .utils import *


def index(request):
    return render(request, 'pm/index.html')

@login_required
def orders(request):
    if request.method == 'POST' and request.is_ajax():
        data = {"message": 'I have done nothing'}
        action = request.POST.get('action')
        if action == 'create-exec-order':
            order = OrderUtils.get_exec_order()
            data = {"exec_order_number": str(order.number)}
        elif action == "add-to-exec-order":
            order_id = request.POST.get('order_id')
            data = {"message": 'Received: ' + str(order_id) +" "+ str(Order.objects.get(id=order_id))}
        elif action == "status":
            order = Order.objects.get(status=-1)
            data = {"status": "ok", "exec_order_number": str(order.number)}
        return JsonResponse(data)

    order_target = request.GET.get('target')
    if order_target == None:
        all_orders_list = Order.objects.filter(target='').order_by('-date')
    elif order_target == 'ALL':
        all_orders_list = Order.objects.all().order_by('-date')
    else:
        all_orders_list = Order.objects.filter(target=str(order_target)).order_by('-date')
    context = {
        'all_orders_list' : all_orders_list,
        'target' : order_target,
    }
    return render(request, 'pm/orders.html', context)


@login_required
def create_order(request):
    if request.method == 'POST':
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('pm:orders'))
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            form.save()
            CounterUtils.update_number('orders')
            return HttpResponseRedirect(reverse('pm:add_products_to_order', args=(order.id,)))
    else:
        form = OrderForm(initial= {"number": str(CounterUtils.next_number('orders'))})
    return render(request, 'pm/create_order.html', {'form': form,})


class OrderDetail(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'pm/order_detail.html'


@login_required
def add_products_to_order(request, orderid):
    order = get_object_or_404(Order, pk=orderid)
    if request.method == 'POST':
        form = OrderEntryForm(request.POST)
        if "done" in request.POST:
            OrderUtils.create_sub_orders(order_id=order.id)
            return HttpResponseRedirect(reverse('pm:order_detail', args=(order.id,)))
        if form.is_valid():
            product = form.save(commit=False)
            product.order = order
            product.save()
            return HttpResponseRedirect(reverse('pm:add_products_to_order', args=(order.id,)))
    else:
        form = OrderEntryForm()
    return render(request, 'pm/add_products_to_order.html', {'form': form, 'order': order})


@login_required
def products(request):
    all_products_list = Product.objects.order_by('ref_code')
    context = {
        'all_products_list': all_products_list,
    }
    return render(request, 'pm/products.html', context)


@login_required
def create_product(request):
    if request.method == 'POST':
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('pm:products'))
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            form.save()
            product.final = True
            return HttpResponseRedirect(reverse('pm:add_components', args=(product.id,)))
    else:
        form = ProductForm()
    return render(request, 'pm/create_product.html', {'form': form})


@login_required
def create_component(request):
    if request.method == 'POST':
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('pm:products'))
        form = ComponentForm(request.POST)
        if form.is_valid():
            product = form.save()
            ProductUtils.create_intermediate_products(product=product)
            return HttpResponseRedirect(reverse('pm:products'))
    else:
        form = ComponentForm()
    return render(request, 'pm/create_component.html', {'form': form})

@login_required
def add_components(request, productid):
    product = get_object_or_404(Product, pk=productid)
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
def inventory(request):
    return HttpResponse("Here goes the stocks management.")

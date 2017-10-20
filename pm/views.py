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
        response = JsonResponse(data, status=500)

        action = request.POST.get('action')
        if action == 'create-or-show-exec-order':
            if not OrderUtils.exec_order_exists():
                order = OrderUtils.get_exec_order()
                data = {
                    "action_performed": 'create',
                    "exec_order_number": str(order.number)
                }
                response = JsonResponse(data)
            else:
                order = OrderUtils.get_exec_order()
                data = {
                    "action_performed": 'show',
                    "exec_order_number": str(order.number),
                    "exec_order_url": str(reverse('pm:order_detail', args=[order.id]))
                }

                response = JsonResponse(data)

        elif action == "add-or-from-exec-order":
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id)
                exec_order = OrderUtils.exec_order_exists()
                orders_in_exec_order = list(exec_order.get_orders().values_list('id', flat=True))

                if int(order.id) not in orders_in_exec_order:
                    exec_order.add_order(order)
                    data = {
                        "action_performed": 'add',
                        "order_number": str(order.number),
                        "exec_order_number": str(exec_order.number)
                    }
                else:
                    exec_order.remove_order(order)
                    data = {
                        "action_performed": 'rm',
                        "order_number": str(order.number),
                        "exec_order_number": str(exec_order.number)}
                response = JsonResponse(data)
            except:
                data = {"message": 'ERROR!'}
                response = JsonResponse(data, status=500)

        elif action == "status":
            order = Order.objects.get(status=-1)
            data = {"status": "ok", "exec_order_number": str(order.number)}
            response = JsonResponse(data)

        elif action == "cancel-exec-order":
            try:
                deleted_order = OrderUtils.delete_execution_order()
                data = {
                    "deleted_order_description": str(deleted_order.description),
                    "deleted_order_id": str(deleted_order.id)
                }
                response = JsonResponse(data)
            except:
                data = {"message": 'ERROR!'}
                response = JsonResponse(data, status=500)
        return response

    order_target = request.GET.get('target')
    if order_target == None:
        all_orders_list = Order.objects.filter(target='').exclude(exec_order=True).order_by('-date')
    elif order_target == 'ALL':
        all_orders_list = Order.objects.exclude(exec_order=True).order_by('-date')
    else:
        all_orders_list = Order.objects.filter(target=str(order_target)).order_by('-date')
    exec_order = OrderUtils.exec_order_exists()
    orders_in_exec_order_ids = []
    if exec_order:
        print(exec_order)
        orders_in_exec_order_ids = list(exec_order.get_orders().values_list('id', flat=True))
    context = {
        'all_orders_list' : all_orders_list,
        'target' : order_target,
        'exec_order' : exec_order,
        'orders_in_exec_order' : orders_in_exec_order_ids
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

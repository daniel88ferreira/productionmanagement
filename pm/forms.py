from django.forms import ModelForm

from .models import *


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['ref_code', 'name', 'color', 'size']


class ComponentForm(ModelForm):
    class Meta:
        model = Product
        fields =  ['ref_code', 'name', 'color', 'size', 'stages']


class QuantityForm(ModelForm):
    class Meta:
        model = Quantity
        fields = ['component', 'quantity']


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['date', 'number', 'description']


class OrderEntryForm(ModelForm):
    class Meta:
        model = OrderEntry
        fields = ['product', 'quantity']

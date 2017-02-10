from __future__ import unicode_literals

from django.forms import ModelForm
from django.db import models


class Product(models.Model):
    ref_code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=20, default='no-color')
    size = models.CharField(max_length=20)
    components = models.ManyToManyField('self', through='Quantity', symmetrical=False, blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.ref_code +': '+ self.name + ', ' + self.color + ', ' + self.size

    def get_quantity_list(self):
        return Quantity.objects.filter(product=self)


class Quantity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_product')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_component')
    quantity = models.IntegerField(default=1)



class ProductForm(ModelForm):
    class Meta:
        model=Product
        fields=['ref_code', 'name', 'color', 'size']

class QuantityForm(ModelForm):
    class Meta:
        model=Quantity
        fields=['component', 'quantity']

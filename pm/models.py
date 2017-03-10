from __future__ import unicode_literals

from multiselectfield import MultiSelectField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from django.db import models

class ProductionStages(models.Model):
    code = models.CharField(max_length=2, unique=True)
    description = models.CharField(max_length=200)
    affected_characteristic = models.CharField(max_length=20)

    def __str__(self):
        return str(self.code) + ':' + str(self.description) + ':' + str(self.affected_characteristic)

    @staticmethod
    def final():
        return ProductionStages.objects.get(id=1)

    @staticmethod
    def get_stages_choices():
        stages = ()
        for stage in ProductionStages.objects.all():
           stages += ((str(stage.code), str(stage.description)),)
        return stages

    @staticmethod
    def get_stages_all_objects():
        return ProductionStages.objects.all().order_by('id')



class Product(models.Model):
    STAGES = ProductionStages.get_stages_choices()

    ref_code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=20, default='raw')
    size = models.CharField(max_length=20)
    final = models.BooleanField(default=False)
    stages = MultiSelectField(choices=STAGES, default=STAGES[0])
    components = models.ManyToManyField('self', through='Quantity', symmetrical=False, blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.ref_code + ': ' + self.name + ', ' + self.color + ', ' + self.size

    def get_components(self):
        return Quantity.objects.filter(product=self)

    def add_component(self, component, quantity):
        new_component = Quantity.objects.create(product=self, component=component, quantity=quantity)
        new_component.save()

    def get_stages(self):
        ordered_stages = []
        for stage in self.STAGES:
            if stage[0] in self.stages:
                ordered_stages.append(stage[0])
        return ordered_stages


class Quantity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_product')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quantity_component')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return str(self.product) + ' | ' + str(self.component) + ' | ' + str(self.quantity)


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['ref_code', 'name', 'color', 'size', 'stages', 'final']
        labels = {
            'final': _('Produto Acabado?'),
        }


class QuantityForm(ModelForm):
    class Meta:
        model = Quantity
        fields = ['component', 'quantity']


class Order(models.Model):
    TARGETS = ProductionStages.get_stages_choices()

    date = models.DateTimeField(default=timezone.now)
    number = models.CharField(max_length=300, unique=True)
    products = models.ManyToManyField(Product, through='ProductByOrder', blank=True)
    description = models.CharField(max_length=300, default='no-description')
    status = models.IntegerField(default=0)
    suborders = models.ManyToManyField('self', symmetrical=False, blank=True)
    target = models.CharField(max_length=2, choices=TARGETS, default=ProductionStages.final().code)

    def __str__(self):
        return '(' + str(self.number) + ')' + ' ' + self.description

    def add_product(self, product, quantity):
        new_product = ProductByOrder.objects.create(order=self, product=product, quantity=quantity)
        new_product.save()

    def get_products(self):
        return ProductByOrder.objects.filter(order=self)

    def get_suborders_all(self):
        return self._get_suborders(self)

    def _get_suborders(self, order):
        suborders = order.suborders
        suborders_id_list = list(suborders.values_list('id', flat=True))
        for suborder_id in suborders_id_list:
            suborders_query_set = self._get_suborders(Order.objects.get(id=suborder_id))
            if suborders_query_set:
                suborders_id_list.extend(list(suborders_query_set.values_list('id', flat=True)))
        return Order.objects.filter(pk__in = suborders_id_list)

    def target_description(self):
        return ProductionStages.objects.get(description=self.target)

    def target_code(self):
        return  ProductionStages.objects.get(description=self.target)


class ProductByOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='ref_order')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_in_order')
    quantity = models.IntegerField(default=1)


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['date', 'number', 'description']


class ProductByOrderForm(ModelForm):
    class Meta:
        model = ProductByOrder
        fields = ['product', 'quantity']


class Counters(models.Model):
    name = models.CharField(max_length=20)
    value = models.IntegerField(default=0)

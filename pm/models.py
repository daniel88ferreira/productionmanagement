from __future__ import unicode_literals

from ProductionElement import ProductionElement
from django.core.exceptions import ObjectDoesNotExist
from multiselectfield import MultiSelectField
from django.utils import timezone
from django.db import models


class ProductionStages(models.Model):
    code = models.CharField(max_length=2, unique=True)
    description = models.CharField(max_length=200)
    affected_characteristic = models.CharField(max_length=20)

    def __str__(self):
        return str(self.code) + ':' + str(self.description) + ':' + str(self.affected_characteristic)

    def get_next(self):
        return ProductionStages.objects.get(id=self.id+1)

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
    # STAGES = (
    #     ('MT', 'Montagem'),
    #     ('PT', 'Pintura'),
    #     ('CP', 'Carpintaria'),
    # )

    ref_code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=20, default='raw')
    size = models.CharField(max_length=20)
    final = models.BooleanField(default=False)
    stages = MultiSelectField(choices=STAGES, default=[STAGES[0][0]])
    components = models.ManyToManyField('self', through='Quantity', symmetrical=False, blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return str(self.ref_code) + ":" + self.name + ":" + self.color + ":" + self.size

    def get_components(self):
        return Quantity.objects.filter(product=self)

    def get_components_from_stage(self, stage):
        components_and_quantities_from_stage = []
        for component_and_quantity in self.get_components_all():
            product = component_and_quantity[0]
            quantity = component_and_quantity[1]
            if str(product.get_stages()[0]) == stage:
                components_and_quantities_from_stage.append([product, quantity])
        return components_and_quantities_from_stage

    def get_components_all(self):
        return self._get_components()

    def _get_components(self, multiplier=1):
        components_and_quantities = []
        for component in self.get_components():
            product = component.component
            quantity = component.quantity * multiplier
            components_and_quantities.append([product, quantity])
            components_and_quantities.extend(product._get_components(quantity))
        return components_and_quantities

    def add_component(self, component, quantity):
        try:
            Quantity.objects.get(product=self, component=component)
            return
        except ObjectDoesNotExist:
            new_component = Quantity.objects.create(product=self, component=component, quantity=quantity)
            new_component.save()

    def get_stages(self):
        ordered_stages = []
        for stage in self.STAGES:
            if stage[0] in self.stages:
                ordered_stages.append(stage[0])
        return ordered_stages


    def get_main_stage(self):
        return self.get_stages()[0]


class Quantity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='qtt_product')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='qtt_component')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return str(self.product) + ':' + str(self.component) + ':' + str(self.quantity)


class Order(models.Model):
    TARGETS = ProductionStages.get_stages_choices()
    # TARGETS = (
    #     ('BS', 'Base'),
    #     ('MT', 'Montagem'),
    #     ('PT', 'Pintura'),
    #     ('CP', 'Carpintaria'),
    # )

    date = models.DateTimeField(default=timezone.now)
    number = models.CharField(max_length=300, unique=True)
    entries = models.ManyToManyField(Product, through='OrderEntry', blank=True)
    description = models.CharField(max_length=300, default='no-description')
    status = models.IntegerField(default=0)
    suborders = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='order_suborders')
    target = models.CharField(max_length=2, choices=TARGETS, default='')
    #target = models.CharField(max_length=2, choices=TARGETS, default='BS')
    exec_order_reference = models.ForeignKey('self', blank=True, null=True, related_name='order_exec_order', on_delete=models.SET_NULL)
    exec_order = models.BooleanField(default=False)

    def __str__(self):
        return str(self.number)+ ':' + str(self.description)

    def get_orders(self):
        if self.exec_order:
            return Order.objects.filter(exec_order_reference=self, target='')
        else:
            raise ValueError('\"' + str(self) + '\" is not an Execution Order')

    def add_order(self, order):
        if self.exec_order:
            if order.target != '':
                orders = [order] + order.get_suborders_all()
            else:
                order.exec_order_reference = self
                order.save()
                orders = order.get_suborders_all()
            for _order in orders:
                _order.exec_order_reference = self
                _order.save()
                for entry in _order.get_entries():
                    self._add_entry_to_exec_order(entry)
        else:
            raise ValueError('\"' + str(self) + '\" is not an Execution Order')

    def remove_order(self, order):
        if self.exec_order:
            order.save()
            if order.target != '':
                orders = [order] + order.get_suborders_all()
            else:
                order.exec_order_reference = None
                order.save()
                orders = order.get_suborders_all()

            for _order in orders:
                _order.exec_order_reference = None
                _order.save()
                exec_order_entries = self.get_entries()
                for entry in _order.get_entries():
                    try:
                        existing_entry = exec_order_entries.get(product=entry.product)
                        existing_entry.quantity -= entry.quantity
                        existing_entry.save()
                        if existing_entry.quantity == 0:
                            existing_entry.delete()
                    except ObjectDoesNotExist:
                        print("ERROR: Something wrong, entry should exist.")
                        continue
        else:
            raise ValueError('\"' + str(self) + '\" is not an Execution Order')

    def _add_entry_to_exec_order(self, entry):
        try:
            existing_entry = OrderEntry.objects.get(order=self, product__name=str(entry.product.name))
            existing_entry.quantity += entry.quantity
            existing_entry.save()
        except ObjectDoesNotExist:
            OrderEntry.objects.create(order=self, product=entry.product, quantity=entry.quantity)

    def executing(self):
        return self.status > 0

    def add_entry(self, product, quantity):
        try:
            existing_entry = OrderEntry.objects.get(order=self, product=product)
            existing_entry.quantity += quantity
            existing_entry.save()
        except ObjectDoesNotExist:
            new_entry = OrderEntry.objects.create(order=self, product=product, quantity=quantity)
            new_entry.save()

    def get_entries(self):
        return OrderEntry.objects.filter(order=self).order_by('order__number')

    def get_suborders_all(self):
        return sorted(Order.objects.filter(pk__in=self._get_suborders(self)), key=self._sort_orders)

    @staticmethod
    def _sort_orders(order):
        return ProductionStages.objects.get(code=order.target).id

    def _get_suborders(self, order):
        suborders = order.suborders
        suborders_id_list = list(suborders.values_list('id', flat=True))
        for suborder_id in suborders_id_list:
            suborders_ids = self._get_suborders(Order.objects.get(id=suborder_id))
            if suborders_ids:
                suborders_id_list.extend(suborders_ids)
        return suborders_id_list

    def target_description(self):
         return ProductionStages.objects.get(code=self.target).description

    def target_code(self):
        return ProductionStages.objects.get(code=self.target).code

    def target_id(self):
        return ProductionStages.objects.get(code=self.target).id


class OrderEntry(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='ref_order')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_in_order')
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return str(self.order.number) + ':' + str(self.product.name) + ':' + str(self.quantity)


class Counters(models.Model):
    name = models.CharField(max_length=20)
    value = models.IntegerField(default=0)

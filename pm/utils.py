
from django.core.exceptions import ObjectDoesNotExist
from ProductionElement import ProductionElement
from .models import ProductionStages, Product, Order, Counters
#from .models import  Product, Order, Counters


class ProductTreeElement():
    def __init__(self, product, quantity, stage):
        self.product = product
        self.quantity = quantity
        self.stage = stage

    def __str__(self):
        return "[" + str(self.product.name) + ":" + str(self.quantity) + ":" + str(self.stage) + "]"


class ProductUtils:
    @staticmethod
    def get_product_tree(product, quantity=1):
        pte = ProductTreeElement(
            product=product,
            quantity=quantity,
            stage=product.get_main_stage()
        )
        product_tree = [pte]
        for component in product.get_components():
            product_tree.extend(ProductUtils.get_product_tree(component.component, component.quantity))
        return product_tree

    @staticmethod
    def create_intermediate_products(product):
        products_to_create = product.get_stages()[1:]
        if len(products_to_create) > 0:
            product.add_component(
                component=ProductUtils._create_intermediate_product(product, products_to_create),
                quantity=1
            )

    @staticmethod
    def _create_intermediate_product(product, stages):
        stage = ProductionStages.objects.get(code=str(stages[0]))
        ref_code = str(product.ref_code).split('@')[0] + '@' + stage.code
        name = str(product.name).split('@')[0] + '@' + stage.code

        try:
            return Product.objects.get(name=name)
        except ObjectDoesNotExist:
            pass


        previous_stage = ProductionStages.objects.get(id=stage.id-1)
        if previous_stage.affected_characteristic == None:
            intermediate_product = Product.objects.create(
                ref_code=ref_code,
                name=name,
                color=product.color,
                size=product.size,
                stages=[stage.code],
            )
        else:
            intermediate_product = Product.objects.create(
                ref_code=ref_code,
                name=name,
                size=product.size,
                stages=[stage.code],
            )
        intermediate_product.save()

        if len(stages) == 1:
            return intermediate_product
        elif len(stages) > 1:
            component = ProductUtils._create_intermediate_product(product=intermediate_product, stages=stages[1:])
            intermediate_product.add_component(component=component, quantity=1)
            intermediate_product.save()
            return intermediate_product


class OrderUtils:
    @staticmethod
    def get_exec_order():
        try:
            exec_order = Order.objects.get(exec_order=True, status=0)
        except ObjectDoesNotExist:
            exec_order = Order.objects.create(
                number='x' + str(CounterUtils.next_number('exec_orders')),
                description="Execution order",
                exec_order=True,
            )
            exec_order.save()
            CounterUtils.update_number('exec_orders')
        return exec_order

    @staticmethod
    def create_sub_orders(order_id):
        order = Order.objects.get(id=order_id)
        prod_elements = []
        for entry in order.get_entries():
            qtt_needed =  entry.quantity - entry.product.stock
            if qtt_needed > 0:
                pe = ProductionElement(product=entry.product,quantity=qtt_needed, target=entry.product.stages[0])
                prod_elements.append(pe)
                prod_elements.extend(OrderUtils._create_all_productionElements(production_element=pe))
        OrderUtils._create_suborders(order=order, production_elements=prod_elements)


    @staticmethod
    def _create_suborders(order, production_elements):
        parent_order = order
        stages = ProductionStages.get_stages_all_objects()
        for stage in stages:
            list_of_production_elements_from_stage = []
            for pe in production_elements:
                if pe.target == stage.code:
                    list_of_production_elements_from_stage.append(pe)
            if len(list_of_production_elements_from_stage) > 0:
                suborder = Order.objects.create(
                    number=str(order.number) + '.' + stage.code,
                    description=str(order.description) + '@' + stage.code,
                    status=order.status,
                    target=stage.code
                )
                for pe in list_of_production_elements_from_stage:
                    suborder.add_new_entry(product=pe.product,quantity=pe.quantity)
                parent_order.suborders.add(suborder)
                parent_order.save()
                parent_order = suborder

    @staticmethod
    def _create_all_productionElements(production_element):
        pe = production_element
        prod_elements = []
        for component in pe.product.get_components():
            qtt_needed = pe.quantity * component.quantity - component.component.stock
            if qtt_needed > 0:
                new_pe = ProductionElement(product=component.component,quantity=qtt_needed, target=component.component.stages[0])
                prod_elements.append(new_pe)
                prod_elements.extend(OrderUtils._create_all_productionElements(production_element=new_pe))
        return prod_elements

    @staticmethod
    def mark_order_done(order_id):
        pass


class CounterUtils:
    @staticmethod
    def next_number(name):
        try:
            value = Counters.objects.get(name=name).value
        except ObjectDoesNotExist:
            counter = Counters.objects.create(name=name, value=0)
            value = counter.value
        return value + 1

    @staticmethod
    def update_number(name):
        try:
            counter = Counters.objects.get(name=name)
            counter.value +=1
            counter.save()
        except ObjectDoesNotExist:
            return ObjectDoesNotExist

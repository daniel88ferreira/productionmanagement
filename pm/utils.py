from django.core.exceptions import ObjectDoesNotExist
from .models import ProductionStages, ProductByOrder, Product, Order, Counters

class ProductUtils:
    @staticmethod
    def create_intermediate_products(product_id):
        product = Product.objects.get(id=product_id)
        for main_component in product.components.all():
            ProductUtils._create_intermediate_product(main_component, main_component.get_stages())

    @staticmethod
    def _create_intermediate_product(product, stages):
        stage_name = str(stages[0])
        ref_code = str(product.ref_code).split('%')[0] + '%' + stage_name
        name = str(product.name).split('%')[0] + '%' + stage_name

        try:
            return Product.objects.get(name=name)
        except ObjectDoesNotExist:
            pass

        current_stage = ProductionStages.objects.get(code=stage_name)
        if current_stage.affected_characteristic == None:
            intermediate_product = Product.objects.create(ref_code=ref_code,
                                                      name=name,
                                                      color=product.color,
                                                      size=product.size,
                                                      stages=[stage_name],
                                                      )
        else:
            intermediate_product = Product.objects.create(ref_code=ref_code,
                                                          name=name,
                                                          size=product.size,
                                                          stages=[stage_name],
                                                          )
        intermediate_product.save()

        if len(stages) == 1:
            return intermediate_product
        elif len(stages) > 1:
            component = ProductUtils._create_intermediate_product(product=intermediate_product, stages=stages[1:])
            intermediate_product.add_component(component=component, quantity=1)
            intermediate_product.save()
            product.add_component(component=intermediate_product, quantity=1)
            product.save()
            return intermediate_product


class OrderUtils:
    @staticmethod
    def create_sub_orders(order_id):
        order = Order.objects.get(id=order_id)

        entries = order.get_products()
        products_to_produce = []
        for entry in entries:
            quantity_to_produce =  entry.quantity - entry.product.stock
            if quantity_to_produce > 0:
                products_to_produce.append([entry.product,quantity_to_produce])

        if len(products_to_produce) > 0:
            target = ProductionStages.objects.get(id=order.target_id() + 1)
            sub_order = Order.objects.create(number=str(order.number) + '.' + str(target.code),
                                         date=order.date,
                                         description=str(order.description) + '@' + str(target.description),
                                         target=target.code)
            for element in products_to_produce:
                sub_order.add_product(product=element[0], quantity=element[1])
            order.suborders.add(sub_order)



    @staticmethod
    def mark_order_done(order_id):
        pass


class CounterUtils:
    @staticmethod
    def get_next_number(name):
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

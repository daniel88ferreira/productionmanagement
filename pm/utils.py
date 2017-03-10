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


        sub_order_type = Product.STAGE_1

        sub_order = Order.objects.create(date=order.date,
                                         number=str(order.number) + '.' + str(sub_order_type),
                                         description='a sub order',
                                         status=0,
                                         type=sub_order_type
                                         )
        order.suborders.add(sub_order)
        order.save()

        p1 = Product.objects.get(id=1)
        po = ProductByOrder.objects.create(order=sub_order,
                                           product = p1,
                                           quantity = 10,
                                           )
        po.save()


        sub_sub_order = Order.objects.create(date=sub_order.date,
                                         number=str(sub_order.number) + '.' + Order.TYPE_PT,
                                         description='a sub sub order',
                                         status=0,
                                         type=Product.STAGE_2
                                            )

        sub_order.suborders.add(sub_sub_order)
        sub_sub_order.save()

        p4 = Product.objects.get(id=2)
        po2 = ProductByOrder.objects.create(order=sub_sub_order,
                                           product=p4,
                                           quantity=100,
                                           )
        po2.save()


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

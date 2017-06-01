from django.test import TestCase
from .utils import *
from django.core import serializers



def print_product_tree(product):
    print("Product TREE for " + product.name)
    for e in ProductUtils.get_product_tree(product):
        print("\t" + e.product.name + ":" + str(e.quantity) + ":" + str(e.stage))

def print_order(order):
    print(order)
    for entry in order.get_entries():
        print('\t- ' + str(entry.product.name) + ': ' + str(entry.quantity))


def print_orders(order):
    print_order(order)
    for suborder in order.get_suborders_all():
        print_order(suborder)

def print_all_base_orders():
    for order in Order.objects.filter(target='').order_by('date'):
        print_order(order)

def print_all_base_orders_with_suborders():
    for order in Order.objects.filter(target='').order_by('date'):
        print_orders(order)


def print_table_data(all_table_objects):
    print(serializers.serialize("json", all_table_objects))

def create_test_products():
    ilharga = Product.objects.create(
        ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
    )
    ilharga.save()
    ProductUtils.create_intermediate_products(product=ilharga)
    mv_regina = Product.objects.create(ref_code=2, name='REGINA', color='Branco', size='80', stages=['MT'])
    mv_regina.add_component(ilharga, 2)
    mv_regina.save()


def create_test_orders():
    ilharga = Product.objects.create(
        ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
    )
    ilharga.save()
    ProductUtils.create_intermediate_products(product=ilharga)

    fundo = Product.objects.create(
        ref_code=2, name='fundo', size='200x300', stages=['CP']
    )
    fundo.save()
    ProductUtils.create_intermediate_products(product=fundo)

    mv_regina = Product.objects.create(ref_code=3, name='REGINA', color='Branco', size='80', stages=['MT'])
    mv_regina.add_component(ilharga, 2)
    mv_regina.save()

    mv_clara = Product.objects.create(ref_code=4, name='Clara', color='Azul', size='80', stages=['MT'])
    mv_clara.add_component(ilharga, 10)
    mv_clara.add_component(fundo, 1)
    mv_clara.save()

    order_1 = Order.objects.create(number=1, description='testing order 1')
    order_1.add_new_entry(mv_regina, 20)
    order_1.save()
    OrderUtils.create_sub_orders(order_id=order_1.id)

    order_2 = Order.objects.create(number=2, description='testing order 2')
    order_2.add_new_entry(mv_clara, 20)
    order_2.save()
    OrderUtils.create_sub_orders(order_id=order_2.id)


class ProductUtilsTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_get_product_tree(self):
        ilharga = Product.objects.create(
            ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
        )
        ilharga.save()
        ProductUtils.create_intermediate_products(ilharga)

        regina = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        regina.add_component(ilharga, 2)
        regina.save()

        #---#

        product_tree = ProductUtils.get_product_tree(regina)
        self.assertEqual(len(product_tree), 3)
        self.assertEqual(product_tree[0].product, Product.objects.get(name="REGINA"))
        self.assertEqual(product_tree[0].quantity, 1)
        self.assertEqual(product_tree[0].stage, 'MT')
        self.assertEqual(product_tree[1].product, Product.objects.get(name="ilharga"))
        self.assertEqual(product_tree[1].quantity, 2)
        self.assertEqual(product_tree[1].stage, 'PT')
        self.assertEqual(product_tree[2].product, Product.objects.get(name="ilharga@CP"))
        self.assertEqual(product_tree[2].quantity, 1)
        self.assertEqual(product_tree[2].stage, 'CP')

        product_tree = ProductUtils.get_product_tree(ilharga)
        self.assertEqual(len(product_tree), 2)
        self.assertEqual(product_tree[0].product, Product.objects.get(name="ilharga"))
        self.assertEqual(product_tree[0].quantity, 1)
        self.assertEqual(product_tree[0].stage, 'PT')
        self.assertEqual(product_tree[1].product, Product.objects.get(name="ilharga@CP"))
        self.assertEqual(product_tree[1].quantity, 1)
        self.assertEqual(product_tree[1].stage, 'CP')

    def test_create_intermediate_products(self):
        component = Product.objects.create(ref_code=1, name='ilharga', size='200x300', stages=['PT', 'CP'])
        component.save()
        ProductUtils.create_intermediate_products(component)
        ilharga = Product.objects.get(ref_code=1)
        ilharga_components = ilharga.get_components()
        self.assertIs(len(ilharga_components), 1)
        ilharga_cp = ilharga_components[0].component
        self.assertEqual(ilharga_cp.name, 'ilharga@CP')
        self.assertEqual(ilharga_cp.ref_code, '1@CP')
        self.assertEqual(ilharga_cp.stages, ['CP'])

        self.assertIs(len(ilharga_cp.get_components()),0)

    def test_create_intermediate_products_with_just_one_stage(self):
        fundo = Product.objects.create(
            ref_code=2, name='fundo', color='Branco', size='200x300', stages=['CP']
        )
        fundo.save()
        self.assertEqual(len(ProductUtils.get_product_tree(fundo)), 1)
        ProductUtils.create_intermediate_products(fundo)
        #--- All Set ---#
        product = Product.objects.get(name='fundo')
        self.assertEqual(len(product.get_components()), 0)
        self.assertEqual(len(ProductUtils.get_product_tree(fundo)), 1)


    def test_create_intermediate_products_should_replace_affected_characteristic_with_default_value(self):
        ilharga = Product.objects.create(
            ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
        )
        ilharga.save()
        ProductUtils.create_intermediate_products(product=ilharga)
        sub_component = ilharga.get_components()[0].component
        self.assertEqual(sub_component.stages, ['CP'])
        self.assertEqual(sub_component.color, 'raw')

    def test_create_intermediate_products_should_replace_affected_characteristic_with_default_value_multiple_affected(self):
        #TODO
        pass

    def test_create_intermediate_products_should_not_create_duplicate_objects(self):
        component = Product.objects.create(
            ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
        )
        component.save()
        ProductUtils.create_intermediate_products(component)
        ProductUtils.create_intermediate_products(component)
        ProductUtils.create_intermediate_products(component)

        product_tree = ProductUtils.get_product_tree(component)
        self.assertEqual(len(product_tree), 2)


class OrderUtilsTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_get_exec_order_should_create_an_order_if_there_is_no_exec_order(self):
        order = OrderUtils.get_exec_order()
        self.assertEqual(order.exec_order, True)
        self.assertEqual(order.target, '')
        self.assertEqual(str(order.exec_order_reference), 'pm.Order.None')

    def test_get_exec_order_should_not_create_an_order_if_there_is_one_opened(self):
        order = OrderUtils.get_exec_order()
        self.assertEqual(order.exec_order, True)
        order_2 =  OrderUtils.get_exec_order()
        self.assertEqual(str(order), str(order_2))

        ## set order to execution status
        order.status = 1
        order.save()
        order_2 = OrderUtils.get_exec_order()
        self.assertNotEqual(str(order), str(order_2))

    def test_create_sub_orders_when_stock_for_components_exist(self):
        ilharga = Product.objects.create(
            ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
        )
        ilharga.save()

        ProductUtils.create_intermediate_products(product=ilharga)

        mv_regina = Product.objects.create(ref_code=2, name='REGINA',  color='Branco', size='80', stages=['MT'])
        mv_regina.add_component(ilharga, 2)
        mv_regina.save()

        ilharga = Product.objects.get(name='ilharga')
        ilharga.stock = 20 # All stock needed
        ilharga.save()

        order = Order.objects.create(number=1, description='testing order')
        order.add_new_entry(product=mv_regina, quantity=10)
        order.save()

        OrderUtils.create_sub_orders(order_id=order.id)

        # ---- All Set ---#
        order = Order.objects.get(number=1)
        suborders = order.get_suborders_all()

        self.assertEqual(len(suborders),1)

        suborder = suborders[0]
        self.assertEqual(suborder.target, 'MT')

        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='REGINA'))
        self.assertEqual(entry.quantity, 10)

    def test_create_sub_orders_when_some_stock_for_components_exist(self):
        ilharga = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP'])
        ilharga.save()
        ProductUtils.create_intermediate_products(product=ilharga)
        mv_regina = Product.objects.create(ref_code=2, name='REGINA', size='80', color='Branco', stages=['MT'])
        mv_regina.add_component(ilharga, 2)
        mv_regina.save()

        ilharga = Product.objects.get(name='ilharga')
        ilharga.stock = 18
        ilharga.save()

        order = Order.objects.create(number=1, description='testing order')
        order.add_new_entry(product=mv_regina, quantity=10)
        order.save()

        OrderUtils.create_sub_orders(order_id=order.id)

        # ---- All Set ---#
        order = Order.objects.get(number=1)
        suborders = order.get_suborders_all()

        self.assertEqual(len(suborders), 3) # MT and PT and CP

        suborder = suborders[0]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='REGINA'))
        self.assertEqual(entry.quantity, 10)

        suborder = suborders[1]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga'))
        self.assertEqual(entry.quantity, 2)

        suborder = suborders[2]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga@CP'))
        self.assertEqual(entry.quantity, 2)



    def test_create_sub_orders_with_some_stock_in_first_stage(self):
        # --- Set up ---#
        ilharga = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300',
                                         stages=['PT', 'CP'])
        ilharga.save()
        ProductUtils.create_intermediate_products(product=ilharga)

        mv_regina = Product.objects.create(ref_code=2, name='REGINA', color='Branco', size='80', stages=['MT'])
        mv_regina.add_component(ilharga, 2)
        mv_regina.save()

        ilharga = Product.objects.get(name='ilharga')
        ilharga.stock = 10
        ilharga.save()

        ilharga_CP = Product.objects.get(name='ilharga@CP')
        ilharga_CP.stock = 3
        ilharga_CP.save()

        order = Order.objects.create(number=1, description='testing order')
        order.add_new_entry(product=mv_regina, quantity=10)
        order.save()

        OrderUtils.create_sub_orders(order_id=order.id)

        # ---- All Set ---#
        order = Order.objects.get(number=1)
        suborders = order.get_suborders_all()
        self.assertEqual(len(suborders), 3)  # MT and PT and CP

        suborder = suborders[0]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='REGINA'))
        self.assertEqual(entry.quantity, 10)

        suborder = suborders[1]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga'))
        self.assertEqual(entry.quantity, 10)

        suborder = suborders[2]
        self.assertEqual(len(suborder.get_entries()), 1)
        entry = suborder.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga@CP'))
        self.assertEqual(entry.quantity, 7)


    def test_create_sub_orders_should_create_orders_for_all_stages_if_no_stock(self):
        #--- Set up ---#
        ilharga = Product.objects.create(
            ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP']
        )
        ilharga.save()
        ProductUtils.create_intermediate_products(product=ilharga)

        fundo = Product.objects.create(
            ref_code=2, name='fundo', size='200x300', stages=['CP']
        )
        fundo.save()
        ProductUtils.create_intermediate_products(product=fundo)


        mv_regina = Product.objects.create(ref_code=3, name='REGINA', size='80', stages=['MT'])
        mv_regina.add_component(ilharga, 2)
        mv_regina.add_component(fundo, 1)
        mv_regina.save()

        order = Order.objects.create(number=1, description='testing order')
        order.add_new_entry(product=mv_regina, quantity=10)
        order.save()

        OrderUtils.create_sub_orders(order_id=order.id)

        # ---- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target, '')

        suborders = order.get_suborders_all()
        self.assertEqual(len(suborders), 3)
        self.assertEqual(suborders[0].target, 'MT')
        self.assertEqual(suborders[1].target, 'PT')
        self.assertEqual(suborders[2].target, 'CP')

        suborder_MT = suborders[0]
        self.assertEqual(len(suborder_MT.get_entries()), 1)
        self.assertEqual(str(suborder_MT.number), '1.MT')
        entry = suborder_MT.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='REGINA'))
        self.assertEqual(entry.quantity, 10)

        suborder_PT = suborders[1]
        self.assertEqual(len(suborder_PT.get_entries()), 1)
        self.assertEqual(str(suborder_PT.number), '1.PT')
        entry = suborder_PT.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga'))
        self.assertEqual(entry.quantity, 20)

        suborder_CP = suborders[2]
        self.assertEqual(len(suborder_CP.get_entries()), 2)
        self.assertEqual(str(suborder_CP.number), '1.CP')
        entry = suborder_CP.get_entries()[0]
        self.assertEqual(entry.product, Product.objects.get(name='ilharga@CP'))
        self.assertEqual(entry.quantity, 20)
        entry = suborder_CP.get_entries()[1]
        self.assertEqual(entry.product, Product.objects.get(name='fundo'))
        self.assertEqual(entry.quantity, 10)
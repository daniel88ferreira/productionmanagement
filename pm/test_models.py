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



class ProductTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_create_new_product_stage_default(self):
        product = Product.objects.create(ref_code=1, name='Regina', size='80')
        product.save()
        self.assertEqual(['MT'], product.stages)


class ProductMethodsTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_add_component(self):
        component = Product.objects.create(ref_code=1, name='ilharga', size='200x300', stages=['PT', 'CP'])
        component.save()
        product = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        product.add_component(component, 2)
        product.save()

        product = Product.objects.get(name='REGINA')
        components = product.get_components()
        number_of_components = len(components)
        self.assertIs(number_of_components, 1)
        self.assertEquals(str(components[0].component.name), 'ilharga')

    def test_get_stages_should_order_result_as_initially_defined(self):
        product = Product.objects.create(ref_code=1, name='ilharga', size='200x300', stages=['CP', 'MT', 'PT'])
        product.save()

        product = Product.objects.get(ref_code=1)
        self.assertEquals(product.get_stages(), ['MT', 'PT', 'CP'])
        self.assertNotEquals(product.get_stages(), ['CP', 'MT', 'PT', 'BS'])

    def test_get_components_all_should_return_product_tree(self):
        ilharga = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP'])
        ilharga.save()
        fundo = Product.objects.create(ref_code=2, name='fundo', color='Branco', size='200x300',
                                           stages=['CP'])
        fundo.save()

        product = Product.objects.create(ref_code=3, name='REGINA', size='80', stages=['MT'])
        product.add_component(ilharga, 2)
        product.save()
        product.add_component(fundo, 1)
        product.save()

        #Starting to create intermediate products
        ref_code = str(ilharga.ref_code).split('@')[0] + '@' + 'PT'
        name = str(ilharga.name).split('@')[0] + '@' + 'PT'

        ilharga_PT = Product.objects.create(ref_code=ref_code,
                                                      name=name,
                                                      color=ilharga.color,
                                                      size=ilharga.size,
                                                      stages=['PT'],
                                                      )
        ilharga.add_component(component=ilharga_PT,quantity=1)
        ilharga.save()

        ref_code = str(ilharga_PT.ref_code).split('@')[0] + '@' + 'CP'
        name = str(ilharga_PT.name).split('@')[0] + '@' + 'CP'
        ilharga_CP = Product.objects.create(ref_code=ref_code,
                               name=name,
                               color=ilharga_PT.color,
                               size=ilharga_PT.size,
                               stages=['CP'],
                               )
        ilharga_CP.save()
        ilharga_PT.add_component(component=ilharga_CP, quantity=1)
        ilharga_PT.save()

        ref_code = str(fundo.ref_code).split('@')[0] + '@' + 'CP'
        name = str(fundo.name).split('@')[0] + '@' + 'CP'

        fundo_CP = Product.objects.create(ref_code=ref_code,
                                            name=name,
                                            color=fundo.color,
                                            size=fundo.size,
                                            stages=['CP'],
                                            )
        fundo_CP.save()
        fundo.add_component(component=fundo_CP, quantity=1)
        fundo.save()

        #--- All Set ---#
        product = Product.objects.get(name='REGINA')

        ilharga = Product.objects.get(name='ilharga')
        ilharga_PT = Product.objects.get(name='ilharga@PT')
        ilharga_CP = Product.objects.get(name='ilharga@CP')

        fundo = Product.objects.get(name='fundo')
        fundo_CP = Product.objects.get(name='fundo@CP')

        expected_tree = [[ilharga, 2],[ilharga_PT, 2], [ilharga_CP, 2], [fundo, 1], [fundo_CP, 1]]
        product_tree = product.get_components_all()
        self.assertEqual(len(product_tree), len(expected_tree))
        result = all(element in product_tree for element in expected_tree)
        self.assertEqual(result, True)

    def test_get_components_from_stage(self):
        ilharga = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300',
                                         stages=['PT','CP'])
        ilharga.save()

        ProductUtils.create_intermediate_products(product=ilharga)

        fundo = Product.objects.create(ref_code=2, name='fundo', color='Branco', size='200x300',
                                       stages=['CP'])
        fundo.save()
        ProductUtils.create_intermediate_products(product=fundo)

        product = Product.objects.create(ref_code=3, name='REGINA', size='80', stages=['MT'])
        product.add_component(ilharga, 2)
        product.save()
        product.add_component(fundo, 1)
        product.save()


        #--- ALL SET ---#
        ilharga = Product.objects.get(ref_code=1)
        ilharga_PT = Product.objects.get(name='ilharga')

        regina = Product.objects.get(ref_code=3)
        fundo_CP = Product.objects.get(name='fundo')
        ilharga_CP = Product.objects.get(name='ilharga@CP')

        component_and_quantity = regina.get_components_from_stage(stage='PT')
        self.assertEqual(len(component_and_quantity), 1)
        self.assertEqual(component_and_quantity, [[ilharga_PT, 2]])

        component_and_quantity = regina.get_components_from_stage(stage='CP')
        self.assertEqual(len(component_and_quantity), 2)
        self.assertEqual(component_and_quantity, [[ilharga_CP, 2],[fundo_CP, 1]])


class OrderMethodsTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_add_order_with_regular_and_suborder(self):
        create_test_orders()
        exec_order = Order.objects.create(
            number='x' + str(CounterUtils.next_number('exec_orders')),
            description="Execution order",
            exec_order=True,
        )
        exec_order.save()

        order = Order.objects.get(number='2')
        suborder = Order.objects.get(number='1.PT')

        exec_order.add_order(order)
        exec_order.add_order(suborder)

        print_order(exec_order)
        entries = exec_order.get_entries()
        self.assertEqual(len(entries), 4)

        self.assertEqual(entries[0].product.name, 'Clara')
        self.assertEqual(entries[0].quantity, 20)

        self.assertEqual(entries[1].product.name, 'ilharga')
        self.assertEqual(entries[1].quantity, 240)

        self.assertEqual(entries[2].product.name, 'ilharga@CP')
        self.assertEqual(entries[2].quantity, 240)

        self.assertEqual(entries[3].product.name, 'fundo')
        self.assertEqual(entries[3].quantity, 20)


    def test_add_order_with_two_regular_orders(self):
        create_test_orders()
        exec_order = Order.objects.create(
            number='x' + str(CounterUtils.next_number('exec_orders')),
            description="Execution order",
            exec_order=True,
        )
        exec_order.save()

        for order in Order.objects.filter(target=''):
            exec_order.add_order(order)
            self.assertNotEqual(str(order.exec_order_reference), 'pm.Order.None')

        entries = exec_order.get_entries()
        self.assertEqual(len(entries), 5)

        self.assertEqual(entries[0].product.name, 'REGINA')
        self.assertEqual(entries[0].quantity, 20)

        self.assertEqual(entries[1].product.name, 'ilharga')
        self.assertEqual(entries[1].quantity, 240)

        self.assertEqual(entries[2].product.name, 'ilharga@CP')
        self.assertEqual(entries[2].quantity, 240)

        self.assertEqual(entries[3].product.name, 'Clara')
        self.assertEqual(entries[3].quantity, 20)

        self.assertEqual(entries[4].product.name, 'fundo')
        self.assertEqual(entries[4].quantity, 20)

    def test_add_order_with_suborder(self):
        create_test_orders()
        exec_order = Order.objects.create(
            number='x' + str(CounterUtils.next_number('exec_orders')),
            description="Execution order",
            exec_order=True,
        )
        exec_order.save()

        order = Order.objects.get(number='2.MT')
        exec_order.add_order(order)
        entries = exec_order.get_entries()

        self.assertEqual(len(entries), 4)

        self.assertEqual(entries[0].product.name, 'Clara')
        self.assertEqual(entries[0].quantity, 20)

        self.assertEqual(entries[1].product.name, 'ilharga')
        self.assertEqual(entries[1].quantity, 200)

        self.assertEqual(entries[2].product.name, 'ilharga@CP')
        self.assertEqual(entries[2].quantity, 200)

        self.assertEqual(entries[3].product.name, 'fundo')
        self.assertEqual(entries[3].quantity, 20)


    def test_add_order_raises_exception(self):
        '''
        If it's not and Execution Order
        Should raise ValueError
        '''
        create_test_orders()
        order = Order.objects.create(
            number='x' + str(CounterUtils.next_number('exec_orders')),
            description="Execution order",
            exec_order=False,
        )
        order.save()
        order_to_add = Order.objects.filter(target='')[0]
        self.assertRaises(ValueError, order.add_order, order=order_to_add)


    def test_add_new_entry(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1)
        order.add_new_entry(product=product, quantity=2)
        order.save()

        order = Order.objects.get(number=1)
        products = order.get_entries()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product.name, "REGINA")

    def test_get_products_should_return_all_products_in_order(self):
        product_regina = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product_regina.save()
        product_maria = Product.objects.create(ref_code=2, name='MARIA', size='60', stages=['MT'])
        product_maria.save()
        order = Order.objects.create(number=1)
        order.add_new_entry(product=product_regina, quantity=1)
        order.add_new_entry(product=product_maria, quantity=2)
        order.save()

        order = Order.objects.get(number=1)
        products = order.get_entries()
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].product.name, "REGINA")
        self.assertEqual(products[0].quantity, 1)
        self.assertEqual(products[1].product.name, "MARIA")
        self.assertEqual(products[1].quantity, 2)

    def test_get_suborders_all_with_suborder_should_all_bellow_stages_orders_ordered_by_stage(self):
        create_test_orders()
        suborder = Order.objects.get(number='2.MT')
        suborders = suborder.get_suborders_all()

        self.assertEqual(suborders[0].target_code(), 'PT')
        self.assertEqual(suborders[1].target_code(), 'CP')

    def test_get_suborders_all_should_return_orders_created_for_other_stages_ordered_by_stage(self):

        #### SET UP ####
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()

        sub_sub_sub_order = Order.objects.create(number=4, target='CP')
        sub_sub_sub_order.add_new_entry(product=product, quantity=1000)
        sub_sub_sub_order.save()

        sub_sub_order = Order.objects.create(number=3, target='PT')
        sub_sub_order.add_new_entry(product=product, quantity=100)
        sub_sub_order.suborders.add(sub_sub_sub_order)
        sub_sub_order.save()

        sub_order = Order.objects.create(number=2, target='MT')
        sub_order.add_new_entry(product=product, quantity=10)
        sub_order.suborders.add(sub_sub_order)
        sub_order.save()

        order = Order.objects.create(number=1, target='BS')
        order.add_new_entry(product=product, quantity=1)
        order.suborders.add(sub_order)
        order.save()

        #### ALL SET ####

        order = Order.objects.get(number=1)
        for idx,sub_order in enumerate(order.get_suborders_all()):
            sub_order_number = idx + 2 # expected_numbers = [2,3,4]
            self.assertEqual(sub_order.number, str(sub_order_number))


    def test_add_suborder(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1)
        order.add_new_entry(product=product, quantity=2)
        order.save()

        sub_order = Order.objects.create(number=2)
        sub_order.add_new_entry(product=product, quantity=10)
        sub_order.save()

        order.suborders.add(sub_order)
        order.save()

        suborders = order.suborders.all()
        self.assertEqual(len(suborders), 1)
        self.assertEqual(suborders[0].number, str(2))

    def test_target_code_should_return_str_target_code(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1, target='PT')
        order.add_new_entry(product=product, quantity=100)
        order.save()

        #--- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target_code(), 'PT')

    def test_target_description_should_return_str_target_description(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1, target='PT')
        order.add_new_entry(product=product, quantity=100)
        order.save()

        # --- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target_description(), 'Pintura')


class ProductionStagesTests(TestCase):
    fixtures = ['pm/production_stages.json']

    def test_get_stages_choices(self):
        STAGES = (
            ('MT', 'Montagem'),
            ('PT', 'Pintura'),
            ('CP', 'Carpintaria'),
        )
        self.assertEqual(ProductionStages.get_stages_choices(), STAGES)

    def test_get_stages_all_objects(self):
        self.assertQuerysetEqual(
            list(ProductionStages.get_stages_all_objects()),
            list(['<ProductionStages: MT:Montagem:>',
                  '<ProductionStages: PT:Pintura:color>','<ProductionStages: CP:Carpintaria:>'])
        )

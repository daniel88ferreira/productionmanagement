from django.test import TestCase
from .utils import *
# Create your tests here.



class ProductMethodsTests(TestCase):
    fixtures = ['production_stages.json']

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
        product = Product.objects.create(ref_code=1, name='ilharga', size='200x300', stages=['CP', 'MT', 'PT', 'BS'])
        product.save()

        product = Product.objects.get(ref_code=1)
        self.assertEquals(product.get_stages(), ['BS', 'MT', 'PT', 'CP'])
        self.assertNotEquals(product.get_stages(), ['CP', 'MT', 'PT', 'BS'])


class OrderMethodsTests(TestCase):
    fixtures = ['production_stages.json']

    def test_add_product(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1)
        order.add_product(product=product, quantity=2)
        order.save()

        order = Order.objects.get(number=1)
        products = order.get_products()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product.name, "REGINA")

    def test_get_products_should_return_all_products_in_order(self):
        product_regina = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product_regina.save()
        product_maria = Product.objects.create(ref_code=2, name='MARIA', size='60', stages=['MT'])
        product_maria.save()
        order = Order.objects.create(number=1)
        order.add_product(product=product_regina, quantity=1)
        order.add_product(product=product_maria, quantity=2)
        order.save()

        order = Order.objects.get(number=1)
        products = order.get_products()
        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].product.name, "REGINA")
        self.assertEqual(products[0].quantity, 1)
        self.assertEqual(products[1].product.name, "MARIA")
        self.assertEqual(products[1].quantity, 2)

    def test_get_suborders_all_should_return_orders_created_for_other_stages_ordered_by_stage(self):

        #### SET UP ####
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()

        sub_sub_sub_order = Order.objects.create(number=4, target='CP')
        sub_sub_sub_order.add_product(product=product, quantity=1000)
        sub_sub_sub_order.save()

        sub_sub_order = Order.objects.create(number=3, target='PT')
        sub_sub_order.add_product(product=product, quantity=100)
        sub_sub_order.suborders.add(sub_sub_sub_order)
        sub_sub_order.save()

        sub_order = Order.objects.create(number=2, target='MT')
        sub_order.add_product(product=product, quantity=10)
        sub_order.suborders.add(sub_sub_order)
        sub_order.save()

        order = Order.objects.create(number=1, target='BS')
        order.add_product(product=product, quantity=1)
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
        order.add_product(product=product, quantity=2)
        order.save()

        sub_order = Order.objects.create(number=2)
        sub_order.add_product(product=product, quantity=10)
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
        order.add_product(product=product, quantity=100)
        order.save()

        #--- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target_code(), 'PT')

    def test_target_description_should_return_str_target_description(self):
        product = Product.objects.create(ref_code=1, name='REGINA', size='80', stages=['MT'])
        product.save()
        order = Order.objects.create(number=1, target='PT')
        order.add_product(product=product, quantity=100)
        order.save()

        # --- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target_description(), 'Pintura')



class ProductUtilsTests(TestCase):
    fixtures = ['production_stages.json']

    def test_create_intermediate_products(self):
        component = Product.objects.create(ref_code=1, name='ilharga', size='200x300', stages=['PT', 'CP'])
        component.save()
        product = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        product.add_component(component, 2)
        product.save()

        product = Product.objects.get(name='REGINA')
        ProductUtils.create_intermediate_products(product.id)

        component = Product.objects.get(ref_code=1)
        sub_components = component.get_components()
        self.assertIs(len(sub_components), 1)
        sub_component = sub_components[0].component
        self.assertEqual(sub_component.name, 'ilharga%PT')
        self.assertEqual(sub_component.ref_code,'1%PT')
        self.assertEqual(sub_component.stages,['PT'])

        sub_components=sub_component.get_components()
        self.assertIs(len(sub_components), 1)
        sub_component = sub_components[0].component
        self.assertEqual(sub_component.name, 'ilharga%CP')
        self.assertEqual(sub_component.ref_code, '1%CP')
        self.assertEqual(sub_component.stages, ['CP'])

        self.assertIs(len(sub_component.get_components()),0)


    def test_create_intermediate_products_should_replace_affected_characteristic_with_default_value(self):
        component = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300',
                                           stages=['PT', 'CP'])
        component.save()
        product = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        product.add_component(component, 2)
        product.save()

        product = Product.objects.get(name='REGINA')
        ProductUtils.create_intermediate_products(product.id)

        component = product.get_components()[0].component

        sub_component = component.get_components()[0].component
        self.assertEqual(sub_component.stages, ['PT'])
        self.assertEqual(sub_component.color, 'raw')

        component=sub_component
        sub_component = component.get_components()[0].component
        self.assertEqual(sub_component.stages, ['CP'])
        self.assertEqual(sub_component.color, 'raw')

    def test_create_intermediate_products_should_replace_affected_characteristic_with_default_value_multiple_affected(self):
        #TODO
        pass

    def test_create_intermediate_products_should_not_create_duplicate_objects(self):
        component = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300', stages=['PT', 'CP'])
        component.save()

        product = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        product.add_component(component, 2)
        product.save()

        product = Product.objects.get(name='REGINA')
        ProductUtils.create_intermediate_products(product.id)

        product = Product.objects.create(ref_code=3, name='MARIA', size='80', stages=['MT'])
        product.add_component(component, 2)

        product = Product.objects.get(name='MARIA')
        ProductUtils.create_intermediate_products(product.id)


        component_from_regina = Product.objects.get(name='REGINA').get_components()[0].component
        component_from_maria = Product.objects.get(name='MARIA').get_components()[0].component
        self.assertIs(component_from_regina.id, component_from_maria.id)

        component_from_regina = component_from_regina.get_components()[0].component
        component_from_maria = component_from_maria.get_components()[0].component
        self.assertIs(component_from_regina.id, component_from_maria.id)

class OrderUtilsTests(TestCase):
    fixtures = ['production_stages.json']

    def test_create_sub_orders_should_create_orders_for_all_stages_if_no_stock(self):

        #--- Set up ---#
        component = Product.objects.create(ref_code=1, name='ilharga', color='Branco', size='200x300',
                                           stages=['PT', 'CP'])
        component.save()
        product = Product.objects.create(ref_code=2, name='REGINA', size='80', stages=['MT'])
        product.add_component(component, 2)
        product.save()
        ProductUtils.create_intermediate_products(product_id=product.id)
        order = Order.objects.create(number=1, description='testing order')
        order.add_product(product=product, quantity=10)
        order.save()

        OrderUtils.create_sub_orders(order_id=order.id)

        # ---- All Set ---#
        order = Order.objects.get(number=1)
        self.assertEqual(order.target, 'BS')

        suborders = order.get_suborders_all()
        print(suborders)
        self.assertEqual(len(suborders), 3)
        self.assertEqual(suborders[0].target, 'MT')
        self.assertEqual(suborders[1].target, 'PT')
        self.assertEqual(suborders[2].target, 'CP')



class ProductionStagesTests(TestCase):
    fixtures = ['production_stages.json']

    def test_get_stages_choices(self):
        STAGES = (
            ('BS', 'Base'),
            ('MT', 'Montagem'),
            ('PT', 'Pintura'),
            ('CP', 'Carpintaria'),
        )
        self.assertEqual(ProductionStages.get_stages_choices(), STAGES)

    def test_get_stages_all_objects(self):
        self.assertQuerysetEqual(
            list(ProductionStages.get_stages_all_objects()),
            list(['<ProductionStages: BS:Base:>','<ProductionStages: MT:Montagem:>',
                  '<ProductionStages: PT:Pintura:color>','<ProductionStages: CP:Carpintaria:>'])
        )

from django.test import TestCase

from django.contrib.auth.models import User
from django.urls import reverse


class ViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='daniel', email='dan@gmail.com', password='ferreira123')
        self.client.post(reverse('pm:login'), {'username': 'daniel', 'password': 'ferreira123'})

    def test_index_when_no_login(self):
        '''
        When the user is not logged in.
        Should ask for the user to login.
        '''
        self.client.get(reverse('pm:logout'))
        response = self.client.get(reverse('pm:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please login')
        self.client.post(reverse('pm:login'), {'username': 'daniel', 'password': 'ferreira123'})

    def test_index_when_logged_in(self):
        '''
        Should show the 3 options list. 
        '''
        response = self.client.get(reverse('pm:index'))
        self.assertContains(response, 'Criar e alterar produtos')

    def test_products_view(self):
        '''
        list of products
        '''
        response = self.client.get(reverse('pm:products'))
        #TODO:

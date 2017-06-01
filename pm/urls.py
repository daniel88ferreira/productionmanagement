from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name = 'pm'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.login , {'template_name': 'pm/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': 'pm:index'}, name='logout'),
    url(r'^products/$', views.products, name='products'),
    url(r'^products/create_product/$', views.create_product, name='create_product'),
    url(r'^products/create_component/$', views.create_component, name='create_component'),
    url(r'^products/(?P<productid>[0-9]+)/add_components/$', views.add_components, name='add_components'),
    url(r'^products/(?P<pk>[0-9]+)/details/$', views.ProductDetail.as_view(), name='product_detail'),
    url(r'^products/(?P<pk>[0-9]+)/edit/$', views.ModifyProduct.as_view(), name='modify_product'),
    url(r'^orders/$', views.orders, name='orders'),
    url(r'^orders/create_order/$', views.create_order, name='create_order'),
    url(r'^orders/(?P<orderid>[0-9]+)/add_product_to_order/$', views.add_products_to_order, name='add_products_to_order'),
    url(r'^orders/(?P<pk>[0-9]+)/details/$', views.OrderDetail.as_view(), name='order_detail'),
]

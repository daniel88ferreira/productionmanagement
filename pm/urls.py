from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name = 'pm'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.login , {'template_name': 'pm/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': 'pm:index'}, name='logout'),
    url(r'^products/$', views.products, name='products'),
    url(r'^products/add_product/$', views.create_product, name='add_product'),
    url(r'^products/(?P<productid>[0-9]+)/add_components/$', views.add_components, name='add_components'),
    url(r'^products/(?P<pk>[0-9]+)/details/$', views.ProductDetail.as_view(), name='product_detail'),
    url(r'^products/(?P<pk>[0-9]+)/edit/$', views.ModifyProduct.as_view(), name='modify_product'),
]

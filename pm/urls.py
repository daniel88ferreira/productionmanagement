from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

app_name = 'pm'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', auth_views.login , {'template_name': 'pm/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': 'pm:index'}, name='logout'),
    url(r'^products/$', views.products, name='products'),
    url(r'^products/add_product/$', views.add_product, name='add_product'),
    url(r'^products/(?P<productid>[0-9]+)/add_components/$', views.add_components, name='add_components'),
]

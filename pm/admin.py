from django.contrib import admin

from .models import Product, Quantity


admin.site.register(Product)
admin.site.register(Quantity)

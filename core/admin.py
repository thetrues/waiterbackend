from django.contrib import admin
from core.models import *

models: list = [
    Item,
]

admin.site.register(models)

from django.contrib import admin
from user.models import User

models: list = [User]

admin.site.register(models)

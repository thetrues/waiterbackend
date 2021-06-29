from django.urls import path
from core import views

urlpatterns = [
    path("w/api/items/", views.ItemView.as_view()),
    path("w/api/items/", views.ManageItemView.as_view()),
    path("w/api/items/<int:pk>/item/", views.ManageItemView.as_view()),
]

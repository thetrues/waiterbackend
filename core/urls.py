from django.urls import path
from core import views

urlpatterns = [
    # Items
    path("w/api/items/", views.ItemView.as_view()),
    path("w/api/items/<int:pk>/item/", views.ManageItemView.as_view()),
    # Menus
    path("w/api/menus/", views.MenuView.as_view()),
    path("w/api/menus/<int:pk>/menu/", views.ManageMenuView.as_view()),
    # Additives
    path("w/api/additives/", views.AdditiveView.as_view()),
    path("w/api/additives/<int:pk>/additive/", views.ManageAdditiveView.as_view()),
]

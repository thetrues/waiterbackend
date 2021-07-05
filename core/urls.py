from django.urls import path
from core import views

urlpatterns = [
    # Items
    path("items/", views.ItemView.as_view()),
    path("items/<int:pk>/item/", views.ManageItemView.as_view()),
    # Menus
    path("menus/", views.MenuView.as_view()),
    path("menus/<int:pk>/menu/", views.ManageMenuView.as_view()),
    # Additives
    path("additives/", views.AdditiveView.as_view()),
    path("additives/<int:pk>/additive/", views.ManageAdditiveView.as_view()),
    # InventoryRecord
    path("inventory-records/", views.InventoryRecordView.as_view()),
]

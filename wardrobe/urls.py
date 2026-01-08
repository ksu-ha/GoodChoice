from django.urls import path
from . import views

app_name = 'wardrobe'

urlpatterns = [
    path('', views.home, name='home'),
    path('wardrobe/', views.wardrobe_list, name='wardrobe_list'),
    path('wardrobe/add/', views.add_clothing_item, name='add_item'),
    path('outfits/', views.outfit_list, name='outfit_list'),
    path('outfits/create/', views.create_outfit, name='create_outfit'),
]
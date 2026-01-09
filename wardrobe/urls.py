from django.urls import path
from . import views

app_name = 'wardrobe'

urlpatterns = [
    path('', views.home, name='home'),
    path('wardrobe/', views.wardrobe_list, name='wardrobe_list'),
    path('wardrobe/add/', views.add_clothing_item, name='add_item'),
    path('wardrobe/item/<int:item_id>/', views.get_item_detail, name='item_detail'),
    path('outfits/', views.outfit_list, name='outfit_list'),
    path('outfits/create/', views.create_outfit, name='create_outfit'),
    path('outfits/outfit/<int:outfit_id>/', views.get_outfit_detail, name='outfit_detail'),
    path('analytics/', views.analytics, name='analytics'),
    path('item/<int:item_id>/modal/', views.item_modal_view, name='item_modal'),
    path('outfit/<int:outfit_id>/modal/', views.outfit_modal_view, name='outfit_modal'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('wardrobe/item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('outfits/outfit/<int:outfit_id>/delete/', views.delete_outfit, name='delete_outfit'),
]
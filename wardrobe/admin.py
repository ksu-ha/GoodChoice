from django.contrib import admin
from .models import ClothingItem, Outfit

@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'color', 'occasion', 'rating', 'user')
    list_filter = ('category', 'color', 'occasion', 'rating')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'occasion', 'rating', 'user', 'created_at')
    list_filter = ('occasion', 'rating')
    search_fields = ('name', 'description')
    filter_horizontal = ('items',)
    readonly_fields = ('created_at',)
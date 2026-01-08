from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import ClothingItem, Outfit
from .forms import ClothingItemForm, OutfitForm

def home(request):
    """Главная страница"""
    if request.user.is_authenticated:
        total_items = ClothingItem.objects.filter(user=request.user).count()
        total_outfits = Outfit.objects.filter(user=request.user).count()
    else:
        total_items = 0
        total_outfits = 0
    
    return render(request, 'wardrobe/home.html', {
        'total_items': total_items,
        'total_outfits': total_outfits,
    })

@login_required
def wardrobe_list(request):
    """Страница со всеми вещами в гардеробе"""
    items = ClothingItem.objects.filter(user=request.user)
    return render(request, 'wardrobe/wardrobe_list.html', {
        'items': items
    })

@login_required
def add_clothing_item(request):
    """Форма добавления новой вещи"""
    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Вещь успешно добавлена!')
            return redirect('wardrobe:wardrobe_list')
    else:
        form = ClothingItemForm()
    
    return render(request, 'wardrobe/add_item.html', {'form': form})

@login_required
def outfit_list(request):
    """Страница со всеми образами"""
    outfits = Outfit.objects.filter(user=request.user)
    return render(request, 'wardrobe/outfit_list.html', {
        'outfits': outfits
    })

@login_required
def create_outfit(request):
    """Создание нового образа"""
    if request.method == 'POST':
        form = OutfitForm(request.user, request.POST)
        if form.is_valid():
            outfit = form.save(commit=False)
            outfit.user = request.user
            outfit.save()
            form.save_m2m()
            messages.success(request, 'Образ успешно создан!')
            return redirect('wardrobe:outfit_list')
    else:
        form = OutfitForm(user=request.user)
    
    return render(request, 'wardrobe/create_outfit.html', {'form': form})
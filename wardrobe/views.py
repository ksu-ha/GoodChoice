from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from .models import ClothingItem, Outfit
from .forms import (
    ClothingItemForm, OutfitForm, CustomUserCreationForm, 
    CustomAuthenticationForm, GenerateOutfitForm
)

from .generation_utils import (
    update_compatibility_scores,
    validate_categories_for_generation,
    generate_and_save_outfit,
    prepare_generation_context
)


def home(request):
    """Главная страница"""
    if request.user.is_authenticated:
        total_items = ClothingItem.objects.filter(user=request.user).count()
        total_outfits = Outfit.objects.filter(user=request.user).count()

        recent_items = ClothingItem.objects.filter(user=request.user) \
            .order_by('-created_at')[:4]
        
        recent_outfits = Outfit.objects.filter(user=request.user) \
            .order_by('-created_at')[:4]
    else:
        total_items = 0
        total_outfits = 0
        recent_items = []
        recent_outfits = []
    
    context = {
        'total_items': total_items,
        'total_outfits': total_outfits,
        'recent_items': recent_items,
        'recent_outfits': recent_outfits,
    }
    return render(request, 'wardrobe/home.html', context)

@login_required
def wardrobe_list(request):
    """Страница со всеми вещами в гардеробе"""
    items = ClothingItem.objects.filter(user=request.user)
    
    category = request.GET.get('category', '')
    color = request.GET.get('color', '')
    season = request.GET.get('season', '')
    occasion = request.GET.get('occasion', '')
    min_rating = request.GET.get('min_rating', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    
    if category:
        items = items.filter(category=category)
    if color:
        items = items.filter(color=color)
    if season:
        items = items.filter(season__contains=season)
    if occasion:
        items = items.filter(occasion__contains=occasion) 
    if min_rating:
        items = items.filter(rating__gte=int(min_rating))
    if date_from:
        items = items.filter(created_at__gte=date_from)
    if date_to:
        items = items.filter(created_at__lte=date_to)
    if price_min:
        items = items.filter(price__gte=price_min)
    if price_max:
        items = items.filter(price__lte=price_max)
    
    context = {
        'items': items,
        'current_filters': {
            'category': category,
            'color': color,
            'season': season,
            'occasion': occasion,
            'min_rating': min_rating,
            'date_from': date_from,
            'date_to': date_to,
            'price_min': price_min,
            'price_max': price_max,
        }
    }
    return render(request, 'wardrobe/wardrobe_list.html', context)

@login_required
def add_clothing_item(request):
    """Форма добавления новой вещи"""
    if request.method == 'POST':
        form = ClothingItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            seasons = form.cleaned_data['season']
            item.season = ','.join(seasons)
            occasions = form.cleaned_data['occasion']
            item.occasion = ','.join(occasions)
            item.save()
            messages.success(request, 'Вещь успешно добавлена в гардероб!')
            return redirect('wardrobe:wardrobe_list')
    else:
        form = ClothingItemForm()
    
    context = {'form': form}
    return render(request, 'wardrobe/add_item.html', context)

@login_required
def outfit_list(request):
    """Страница со всеми образами"""
    outfits = Outfit.objects.filter(user=request.user)
    
    occasion = request.GET.get('occasion', '')
    min_rating = request.GET.get('min_rating', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if occasion:
        outfits = outfits.filter(occasion=occasion)
    if min_rating:
        outfits = outfits.filter(rating__gte=int(min_rating))
    if date_from:
        outfits = outfits.filter(created_at__gte=date_from)
    if date_to:
        outfits = outfits.filter(created_at__lte=date_to)
    
    context = {
        'outfits': outfits,
        'current_filters': {
            'occasion': occasion,
            'min_rating': min_rating,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'wardrobe/outfit_list.html', context)

@login_required
def create_outfit(request):
    """Создание нового образа"""
    if request.method == 'POST':
        form = OutfitForm(request.user, request.POST)
        if form.is_valid():
            outfit = form.save(commit=False)
            outfit.user = request.user
            occasions = form.cleaned_data['occasion']
            outfit.occasion = ','.join(occasions)
            outfit.save()
            form.save_m2m()
            messages.success(request, 'Образ успешно создан!')
            return redirect('wardrobe:outfit_list')
    else:
        form = OutfitForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'wardrobe/create_outfit.html', context)

@login_required
def analytics(request):
    """Страница аналитики гардероба"""
    from .models import ClothingItem, Outfit
    from .analytics_utils import (
        get_basic_statistics,
        get_financial_statistics,
        get_usage_statistics,
        get_season_statistics,
        get_recommendations_for_user,
        get_charts_data
    )
    
    items = ClothingItem.objects.filter(user=request.user)
    
    if not items.exists():
        context = {'has_items': False}
        return render(request, 'wardrobe/analytics.html', context)
    
    # Получаем все данные через утилиты
    basic_stats = get_basic_statistics(request.user, ClothingItem, Outfit)
    financial_stats = get_financial_statistics(request.user, ClothingItem)
    usage_stats = get_usage_statistics(request.user, ClothingItem, Outfit)
    season_stats = get_season_statistics(request.user, ClothingItem)
    recommendations, category_counts = get_recommendations_for_user(request.user, ClothingItem, Outfit)
    charts_data = get_charts_data(request.user, ClothingItem)
    
    context = {
        'has_items': True,
        
        # Базовая статистика
        'total_items': basic_stats['total_items'],
        'total_outfits': basic_stats['total_outfits'],
        'avg_rating': basic_stats['avg_rating'],
        
        # Финансовая аналитика
        'total_price': financial_stats['total_price'],
        'avg_price': financial_stats['avg_price'],
        'most_expensive_items': financial_stats['most_expensive_items'],
        'cheapest_items': financial_stats['cheapest_items'],
        'category_budget': financial_stats['category_budget'],
        
        # Статистика использования
        'popular_items': usage_stats['popular_items'],
        'unused_items': usage_stats['unused_items'],
        'usage_percentage': usage_stats['usage_percentage'],
        
        # Сезонная аналитика
        'season_stats': season_stats,
        
        # Рекомендации
        'recommendations': recommendations,
        'category_counts': category_counts,
        
        # Графики
        'color_chart': charts_data['color_chart'],
        'category_chart': charts_data['category_chart'],
        'budget_chart': charts_data['budget_chart']
    }
    return render(request, 'wardrobe/analytics.html', context)

def item_modal_view(request, item_id):
    item = get_object_or_404(ClothingItem, id=item_id)
    return render(request, 'wardrobe/item_modal.html', {'item': item, 'show_delete': False})


def outfit_modal_view(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id)
    return render(request, 'wardrobe/outfit_modal.html', {'outfit': outfit})

def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('wardrobe:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('wardrobe:home')
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    return render(request, 'wardrobe/register.html', context)

def login_view(request):
    """Вход пользователя"""
    if request.user.is_authenticated:
        return redirect('wardrobe:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {username}!')
                next_url = request.GET.get('next', 'wardrobe:home')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    context = {'form': form}
    return render(request, 'wardrobe/login.html', context)

@login_required
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('wardrobe:home')

@login_required
def delete_item(request, item_id):
    """Удаление вещи"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    item_name = item.name
    item.delete()
    messages.success(request, f'Вещь "{item_name}" успешно удалена!')
    return redirect('wardrobe:wardrobe_list')

@login_required
def delete_outfit(request, outfit_id):
    """Удаление образа"""
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    outfit_name = outfit.name
    outfit.delete()
    messages.success(request, f'Образ "{outfit_name}" успешно удален!')
    return redirect('wardrobe:outfit_list')

@login_required
def generate_outfit(request):
    """Главная страница генерации образов"""
    
    user_items_count = ClothingItem.objects.filter(user=request.user).count()
    if user_items_count < 2:
        messages.warning(request, 'Добавьте минимум 2 вещи в гардероб для генерации образов')
        return redirect('wardrobe:add_item')
    
    if request.method == 'POST' and 'generate' in request.POST:
        form = GenerateOutfitForm(request.POST)
        
        if form.is_valid():
            categories = form.cleaned_data['categories']
            request.session['selected_categories'] = categories
            generated_items, error = generate_and_save_outfit(request, categories)
            
            if error:
                messages.error(request, error)
                return redirect('wardrobe:generate_outfit')
            
            context = prepare_generation_context(
                request, 
                form=GenerateOutfitForm(initial={'categories': categories}),
                generated_items=generated_items
            )
            return render(request, 'wardrobe/generate_outfit.html', context)
    
    context = prepare_generation_context(request)

    if request.method == 'POST':
        form = GenerateOutfitForm(request.POST)
        if form.errors:
            context['form'] = form
    
    return render(request, 'wardrobe/generate_outfit.html', context)

@login_required
def regenerate_outfit(request):
    """Генерировать новый образ с теми же категориями"""
    
    saved_categories = request.session.get('selected_categories', [])
    
    if not saved_categories:
        messages.error(request, 'Сначала выберите категории в генераторе')
        return redirect('wardrobe:generate_outfit')
    
    valid_categories, categories_with_items = validate_categories_for_generation(
        request.user, 
        saved_categories
    )
    
    if not valid_categories:
        if len(categories_with_items) < 2:
            messages.error(
                request, 
                f'В сохраненных категориях недостаточно вещей ({len(categories_with_items)} из минимум 2). '
                f'Выберите другие категории.'
            )
        else:
            messages.error(request, 'В сохраненных категориях недостаточно вещей')
        
        return redirect('wardrobe:generate_outfit')
    
    generated_items, error = generate_and_save_outfit(request, saved_categories)
    
    if error:
        messages.error(request, error)
        return redirect('wardrobe:generate_outfit')
    
    context = prepare_generation_context(
        request,
        form=GenerateOutfitForm(initial={'categories': saved_categories}),
        generated_items=generated_items
    )
    
    return render(request, 'wardrobe/generate_outfit.html', context)

@login_required
def rate_outfit(request):
    """Оценить сгенерированный образ"""
    
    if request.method != 'POST' or 'generated_outfit' not in request.session:
        messages.error(request, 'Не удалось оценить образ')
        return redirect('wardrobe:generate_outfit')
    
    from .forms import RateOutfitForm
    
    rating_form = RateOutfitForm(request.POST)
    
    if not rating_form.is_valid():
        messages.error(request, 'Пожалуйста, выберите оценку')
        return redirect('wardrobe:generate_outfit')
    
    rating = int(rating_form.cleaned_data['rating'])
    outfit_data = request.session['generated_outfit']
    item_ids = outfit_data['item_ids']
    
    items = ClothingItem.objects.filter(id__in=item_ids, user=request.user)
    
    if len(items) != len(item_ids):
        messages.error(request, 'Ошибка: некоторые вещи не найдены')
        return redirect('wardrobe:generate_outfit')
    
    update_compatibility_scores(request.user, items, rating)
    
    for item in items:
        item.times_shown += 1
        item.save()
    
    if rating >= 4:
        for item in items:
            item.times_shown = max(0, item.times_shown - 1)
            item.save()
    
    request.session['outfit_rated'] = True
    request.session['last_rating'] = rating
    
    messages.success(request, f'Спасибо за оценку {rating} ★! Система обучилась на ваших предпочтениях.')
    return redirect('wardrobe:generate_outfit')
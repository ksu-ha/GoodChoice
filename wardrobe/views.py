from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
import plotly.express as px
import pandas as pd
from plotly.offline import plot

from .models import ClothingItem, Outfit
from .forms import ClothingItemForm, OutfitForm

def home(request):
    """Главная страница"""
    if request.user.is_authenticated:
        # Статистика для главной
        total_items = ClothingItem.objects.filter(user=request.user).count()
        total_outfits = Outfit.objects.filter(user=request.user).count()
        
        # Самый популярный цвет
        popular_color = ClothingItem.objects.filter(user=request.user) \
            .values('color') \
            .annotate(count=Count('id')) \
            .order_by('-count') \
            .first()
        
        # Самый популярный тип одежды
        popular_category = ClothingItem.objects.filter(user=request.user) \
            .values('category') \
            .annotate(count=Count('id')) \
            .order_by('-count') \
            .first()
        
        # Последние добавленные вещи - ТОЛЬКО 4!
        recent_items = ClothingItem.objects.filter(user=request.user) \
            .order_by('-created_at')[:4]  # ← МЕНЯЕМ С 5 на 4
        
        # Последние добавленные образы - ТОЛЬКО 4!
        recent_outfits = Outfit.objects.filter(user=request.user) \
            .order_by('-created_at')[:4]  # ← МЕНЯЕМ С 5 на 4
    else:
        total_items = 0
        total_outfits = 0
        popular_color = None
        popular_category = None
        recent_items = []
        recent_outfits = []
    
    context = {
        'total_items': total_items,
        'total_outfits': total_outfits,
        'popular_color': popular_color,
        'popular_category': popular_category,
        'recent_items': recent_items,
        'recent_outfits': recent_outfits,
    }
    return render(request, 'wardrobe/home.html', context)

@login_required
def wardrobe_list(request):
    """Страница со всеми вещами в гардеробе"""
    items = ClothingItem.objects.filter(user=request.user)
    
    # Фильтрация
    category = request.GET.get('category', '')
    color = request.GET.get('color', '')
    season = request.GET.get('season', '')
    occasion = request.GET.get('occasion', '')
    min_rating = request.GET.get('min_rating', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if category:
        items = items.filter(category=category)
    if color:
        items = items.filter(color=color)
    if season:
        items = items.filter(season__contains=season)
    if occasion:
        items = items.filter(occasion=occasion)
    if min_rating:
        items = items.filter(rating__gte=int(min_rating))
    if date_from:
        items = items.filter(created_at__gte=date_from)
    if date_to:
        items = items.filter(created_at__lte=date_to)
    
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
            # Преобразуем список сезонов в строку
            seasons = form.cleaned_data['season']
            item.season = ','.join(seasons)
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
    
    # Фильтрация образов
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
            outfit.save()
            form.save_m2m()  # Сохраняем ManyToMany связь
            messages.success(request, 'Образ успешно создан!')
            return redirect('wardrobe:outfit_list')
    else:
        form = OutfitForm(user=request.user)
    
    context = {'form': form}
    return render(request, 'wardrobe/create_outfit.html', context)

@login_required
def analytics(request):
    """Страница аналитики гардероба"""
    items = ClothingItem.objects.filter(user=request.user)
    
    if not items.exists():
        context = {'has_items': False}
        return render(request, 'wardrobe/analytics.html', context)
    
    # График распределения по цветам
    color_data = items.values('color').annotate(count=Count('id')).order_by('-count')
    color_df = pd.DataFrame(list(color_data))
    
    if not color_df.empty:
        color_fig = px.pie(
            color_df, 
            values='count', 
            names='color',
            title='Распределение вещей по цветам',
            color_discrete_map={
                'red': '#FF0000', 'blue': '#0000FF', 'green': '#00FF00',
                'black': '#000000', 'white': '#FFFFFF', 'pink': '#FFC0CB',
                'yellow': '#FFFF00', 'purple': '#800080', 'brown': '#A52A2A',
                'gray': '#808080', 'beige': '#F5F5DC', 'multicolor': '#FF00FF'
            }
        )
        color_fig.update_traces(textposition='inside', textinfo='percent+label')
        color_chart = plot(color_fig, output_type='div')
    else:
        color_chart = None
    
    # График распределения по категориям
    category_data = items.values('category').annotate(count=Count('id')).order_by('-count')
    category_df = pd.DataFrame(list(category_data))
    
    if not category_df.empty:
        category_fig = px.bar(
            category_df,
            x='category',
            y='count',
            title='Количество вещей по категориям',
            labels={'category': 'Категория', 'count': 'Количество'},
            color='count',
            color_continuous_scale='blues'
        )
        category_chart = plot(category_fig, output_type='div')
    else:
        category_chart = None
    
    # Статистика
    total_items = items.count()
    total_outfits = Outfit.objects.filter(user=request.user).count()
    avg_rating = items.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Самые популярные
    most_common_color = items.values('color').annotate(count=Count('id')).order_by('-count').first()
    most_common_category = items.values('category').annotate(count=Count('id')).order_by('-count').first()
    
    context = {
        'has_items': True,
        'total_items': total_items,
        'total_outfits': total_outfits,
        'avg_rating': round(avg_rating, 1),
        'most_common_color': most_common_color,
        'most_common_category': most_common_category,
        'color_chart': color_chart,
        'category_chart': category_chart,
    }
    return render(request, 'wardrobe/analytics.html', context)

@login_required
def get_item_detail(request, item_id):
    """Получить детальную информацию о вещи для модального окна"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
    # Получаем список сезонов как читаемый текст
    seasons_list = []
    if item.season:
        season_mapping = {
            'winter': 'Зима',
            'spring': 'Весна', 
            'summer': 'Лето',
            'autumn': 'Осень'
        }
        for season in item.season.split(','):
            if season in season_mapping:
                seasons_list.append(season_mapping[season])
    
    seasons_text = ', '.join(seasons_list) if seasons_list else 'Не указано'
    
    # Сколько раз эта вещь использовалась в образах
    used_in_outfits = Outfit.objects.filter(items=item, user=request.user).count()
    
    return JsonResponse({
        'success': True,
        'item': {
            'id': item.id,
            'name': item.name,
            'image_url': item.image.url if item.image else None,
            'description': item.description or 'Нет описания',
            'color': item.get_color_display(),
            'color_code': item.color,
            'category': item.get_category_display(),
            'seasons': seasons_text,
            'occasion': item.get_occasion_display(),
            'rating': item.rating,
            'created_at': item.created_at.strftime('%d.%m.%Y %H:%M'),
            'used_in_outfits': used_in_outfits,
        }
    })

@login_required
def get_outfit_detail(request, outfit_id):
    """Получить детальную информацию об образе для модального окна"""
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    
    # Получаем информацию о вещах в образе
    items_data = []
    for item in outfit.items.all():
        items_data.append({
            'id': item.id,
            'name': item.name,
            'image_url': item.image.url if item.image else None,
            'category': item.get_category_display(),
            'color': item.get_color_display(),
            'rating': item.rating,
        })
    
    # Статистика по цветам в образе
    color_stats = {}
    for item in outfit.items.all():
        color = item.get_color_display()
        color_stats[color] = color_stats.get(color, 0) + 1
    
    return JsonResponse({
        'success': True,
        'outfit': {
            'id': outfit.id,
            'name': outfit.name,
            'description': outfit.description or 'Нет описания',
            'occasion': outfit.get_occasion_display(),
            'rating': outfit.rating,
            'created_at': outfit.created_at.strftime('%d.%m.%Y %H:%M'),
            'total_items': outfit.items.count(),
            'items': items_data,
            'color_stats': color_stats,
        }
    })
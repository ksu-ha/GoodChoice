from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Max, Min
from django.http import JsonResponse
import plotly.express as px
import pandas as pd
from plotly.offline import plot
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import ClothingItem, Outfit
from .forms import ClothingItemForm, OutfitForm

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
        items = items.filter(occasion=occasion)
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
    items = ClothingItem.objects.filter(user=request.user)
    
    if not items.exists():
        context = {'has_items': False}
        return render(request, 'wardrobe/analytics.html', context)
    
    # ============ БАЗОВАЯ СТАТИСТИКА ============
    total_items = items.count()
    total_outfits = Outfit.objects.filter(user=request.user).count()
    avg_rating = items.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # ============ ФИНАНСОВАЯ АНАЛИТИКА ============
    # Стоимость всего гардероба (только вещи с ценой)
    price_stats = items.filter(price__isnull=False).aggregate(
        total=Sum('price'),
        avg=Avg('price'),
        max=Max('price'),
        min=Min('price')
    )
    
    total_price = price_stats['total'] or 0
    avg_price = price_stats['avg'] or 0
    
    # Самая дорогая вещь (топ 3)
    most_expensive_items = items.filter(price__isnull=False).order_by('-price')[:3]
    
    # Самая дешевая вещь (топ 3)
    cheapest_items = items.filter(price__isnull=False).order_by('price')[:3]
    
    # Распределение бюджета по категориям
    category_budget = {}
    for category_code, category_name in ClothingItem.CATEGORY_CHOICES:
        category_items = items.filter(category=category_code, price__isnull=False)
        category_total = category_items.aggregate(total=Sum('price'))['total'] or 0
        if category_total > 0:
            category_budget[category_name] = {
                'total': category_total,
                'percent': round((category_total / total_price) * 100, 1) if total_price > 0 else 0,
                'count': category_items.count()
            }
    
    # ============ СТАТИСТИКА ИСПОЛЬЗОВАНИЯ ============
    # Самые популярные вещи (входят в больше всего образов)
    popular_items_data = []
    for item in items:
        outfit_count = Outfit.objects.filter(items=item, user=request.user).count()
        if outfit_count > 0:
            popular_items_data.append({
                'item': item,
                'outfit_count': outfit_count
            })
    popular_items = sorted(popular_items_data, key=lambda x: x['outfit_count'], reverse=True)[:3]
    
    # Неиспользуемые вещи (ни в одном образе)
    unused_items = []
    for item in items:
        outfit_count = Outfit.objects.filter(items=item, user=request.user).count()
        if outfit_count == 0:
            unused_items.append(item)
    unused_items = unused_items[:3]
    
    # Коэффициент использования
    used_items_count = sum(1 for item in items if Outfit.objects.filter(items=item, user=request.user).exists())
    usage_percentage = round((used_items_count / total_items) * 100, 1) if total_items > 0 else 0
    
    # ============ СЕЗОННАЯ АНАЛИТИКА ============
    season_stats = {}
    for season_code, season_name in ClothingItem.SEASON_CHOICES:
        season_count = items.filter(season__contains=season_code).count()
        season_stats[season_name] = {
            'count': season_count,
            'percent': round((season_count / total_items) * 100, 1) if total_items > 0 else 0
        }
    
    # ============ РЕКОМЕНДАЦИИ ============
    recommendations = []
    
    # Проверяем пробелы по категориям
    category_counts = {}
    for category_code, category_name in ClothingItem.CATEGORY_CHOICES:
        count = items.filter(category=category_code).count()
        category_counts[category_name] = count
        
        # Рекомендации по категориям
        if count < 3 and total_items >= 10:
            recommendations.append(f"Мало вещей категории '{category_name}' ({count} шт.)")
    
    # Проверяем вещи без цены
    items_without_price = items.filter(price__isnull=True).count()
    if items_without_price > 0:
        recommendations.append(f"У {items_without_price} вещей не указана цена")
    
    # Проверяем неиспользуемые вещи
    if len(unused_items) >= 3:
        recommendations.append(f"У вас {len(unused_items)}+ вещей не используются в образах")
    
    # Проверяем сезонные пробелы
    for season_name, stats in season_stats.items():
        if stats['percent'] < 15 and total_items >= 10:
            recommendations.append(f"Мало вещей для сезона '{season_name}' ({stats['count']} шт.)")
    
    # ============ ГРАФИКИ (Data Science) ============
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
    
    # ============ КОНТЕКСТ ============
    context = {
        'has_items': True,
        'total_items': total_items,
        'total_outfits': total_outfits,
        'avg_rating': round(avg_rating, 1),
        
        # Финансовая аналитика
        'total_price': total_price,
        'avg_price': round(avg_price, 2) if avg_price else 0,
        'most_expensive_items': most_expensive_items,
        'cheapest_items': cheapest_items,
        'category_budget': category_budget,
        
        # Статистика использования
        'popular_items': popular_items,
        'unused_items': unused_items,
        'usage_percentage': usage_percentage,
        
        # Сезонная аналитика
        'season_stats': season_stats,
        
        # Рекомендации
        'recommendations': recommendations,
        'category_counts': category_counts,
        
        # Графики
        'color_chart': color_chart,
        'category_chart': category_chart,
    }
    return render(request, 'wardrobe/analytics.html', context)

@login_required
def get_item_detail(request, item_id):
    """Получить детальную информацию о вещи для модального окна"""
    item = get_object_or_404(ClothingItem, id=item_id, user=request.user)
    
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


def item_modal_view(request, item_id):
    item = get_object_or_404(ClothingItem, id=item_id)
    return render(request, 'wardrobe/item_modal.html', {'item': item})


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
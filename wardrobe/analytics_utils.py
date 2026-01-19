import pandas as pd
import plotly.express as px
from plotly.offline import plot

from django.db.models import Count, Avg, Sum, Max, Min


def get_basic_statistics(user, ClothingItem, Outfit):
    """Базовая статистика гардероба"""
    items = ClothingItem.objects.filter(user=user)
    
    total_items = items.count()
    total_outfits = Outfit.objects.filter(user=user).count()
    avg_rating = items.aggregate(avg=Avg('rating'))['avg'] or 0
    
    return {
        'total_items': total_items,
        'total_outfits': total_outfits,
        'avg_rating': round(avg_rating, 1),
    }

def get_financial_statistics(user, ClothingItem):
    """Финансовая аналитика"""
    items = ClothingItem.objects.filter(user=user)
    
    # Стоимость всего гардероба
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
    
    return {
        'total_price': total_price,
        'avg_price': round(avg_price, 2) if avg_price else 0,
        'most_expensive_items': most_expensive_items,
        'cheapest_items': cheapest_items,
        'category_budget': category_budget,
    }

def get_usage_statistics(user, ClothingItem, Outfit):
    """Статистика использования вещей"""
    items = ClothingItem.objects.filter(user=user)
    
    # Самые популярные вещи (входят в больше всего образов)
    popular_items_data = []
    for item in items:
        outfit_count = Outfit.objects.filter(items=item, user=user).count()
        if outfit_count > 0:
            popular_items_data.append({
                'item': item,
                'outfit_count': outfit_count
            })
    popular_items = sorted(popular_items_data, key=lambda x: x['outfit_count'], reverse=True)[:3]
    
    # Неиспользуемые вещи (ни в одном образе)
    unused_items = []
    for item in items:
        outfit_count = Outfit.objects.filter(items=item, user=user).count()
        if outfit_count == 0:
            unused_items.append(item)
    unused_items = unused_items[:3]
    
    # Коэффициент использования
    total_items = items.count()
    used_items_count = sum(1 for item in items if Outfit.objects.filter(items=item, user=user).exists())
    usage_percentage = round((used_items_count / total_items) * 100, 1) if total_items > 0 else 0
    
    return {
        'popular_items': popular_items,
        'unused_items': unused_items,
        'usage_percentage': usage_percentage,
    }

def get_season_statistics(user, ClothingItem):
    """Сезонная статистика"""
    items = ClothingItem.objects.filter(user=user)
    total_items = items.count()
    
    season_stats = {}
    for season_code, season_name in ClothingItem.SEASON_CHOICES:
        season_count = items.filter(season__contains=season_code).count()
        season_stats[season_name] = {
            'count': season_count,
            'percent': round((season_count / total_items) * 100, 1) if total_items > 0 else 0
        }
    
    return season_stats

def get_recommendations_for_user(user, ClothingItem, Outfit):
    """Генерация рекомендаций для пользователя"""
    items = ClothingItem.objects.filter(user=user)
    total_items = items.count()
    
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
    unused_items_count = sum(1 for item in items if not Outfit.objects.filter(items=item, user=user).exists())
    if unused_items_count >= 3:
        recommendations.append(f"У вас {unused_items_count}+ вещей не используются в образах")
    
    # Проверяем сезонные пробелы
    season_stats = get_season_statistics(user, ClothingItem)
    for season_name, stats in season_stats.items():
        if stats['percent'] < 15 and total_items >= 10:
            recommendations.append(f"Мало вещей для сезона '{season_name}' ({stats['count']} шт.)")
    
    return recommendations, category_counts

def get_charts_data(user, ClothingItem):
    """Генерация данных для графиков"""
    items = ClothingItem.objects.filter(user=user)
    
    # 1. График распределения по цветам
    color_data = items.values('color').annotate(count=Count('id')).order_by('-count')
    color_df = pd.DataFrame(list(color_data))
    
    if not color_df.empty:
        color_mapping = dict(ClothingItem.COLOR_CHOICES)
        color_df['color_rus'] = color_df['color'].map(color_mapping)
        
        color_fig = px.pie(
            color_df, 
            values='count', 
            names='color_rus',
            title='Распределение вещей по цветам',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        color_fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            marker=dict(line=dict(color='white', width=1))
        )
        color_chart = plot(color_fig, output_type='div')
    else:
        color_chart = None
    
    # 2. График распределения по категориям
    category_data = items.values('category').annotate(count=Count('id')).order_by('-count')
    category_df = pd.DataFrame(list(category_data))
    
    if not category_df.empty:
        category_mapping = dict(ClothingItem.CATEGORY_CHOICES)
        category_df['category_rus'] = category_df['category'].map(category_mapping)
        
        category_fig = px.bar(
            category_df,
            x='category_rus',
            y='count',
            title='Количество вещей по категориям',
            color='category_rus',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        category_fig.update_layout(
            xaxis_title='Категория',
            yaxis_title='Количество вещей'
        )
        category_chart = plot(category_fig, output_type='div')
    else:
        category_chart = None
    
    # 3. График бюджета по категориям
    budget_chart = None
    category_price_data = list(items.filter(price__isnull=False)
        .values('category')
        .annotate(total_price=Sum('price'), count=Count('id')))
    
    if category_price_data:
        budget_df = pd.DataFrame(category_price_data)
        if not budget_df.empty and budget_df['total_price'].sum() > 0:
            category_mapping = dict(ClothingItem.CATEGORY_CHOICES)
            budget_df['category_name'] = budget_df['category'].map(category_mapping)
            
            budget_fig = px.pie(
                budget_df,
                values='total_price',
                names='category_name',
                title='Распределение бюджета по категориям',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            budget_fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='white', width=1))
            )
            budget_chart = plot(budget_fig, output_type='div')
    
    return {
        'color_chart': color_chart,
        'category_chart': category_chart,
        'budget_chart': budget_chart,
    }
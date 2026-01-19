import random
from django import forms
from .models import ClothingItem, Compatibility
from .forms import GenerateOutfitForm, RateOutfitForm


def get_or_create_compatibility(user, item1, item2):
    """Получает или создает запись о совместимости"""
    
    if item1.id > item2.id:
        item1, item2 = item2, item1
    
    compatibility, created = Compatibility.objects.get_or_create(
        user=user,
        item1=item1,
        item2=item2,
        defaults={'score': 0}
    )
    
    return compatibility.score


def generate_outfit_algorithm(user, categories):
    """Алгоритм генерации образов"""
    
    if len(categories) < 2:
        return None
    
    # Сортируем категории в правильном порядке
    category_order = {
        'outer': 1,     # Верхняя одежда
        'dress': 2,     # Костюм/Платье
        'top': 3,       # Верх
        'bottom': 4,    # Низ
        'shoes': 5,     # Обувь
        'accessory': 6  # Аксессуары
    }
    
    sorted_categories = sorted(categories, key=lambda x: category_order.get(x, 7))
    selected_items = []
    
    first_category = sorted_categories[0]
    first_items = ClothingItem.objects.filter(user=user, category=first_category)
    
    if not first_items.exists():
        return None
    
    total_rating = sum(item.rating for item in first_items)
    if total_rating == 0:
        total_rating = len(first_items) * 3
    
    probabilities = [item.rating / total_rating for item in first_items]
    
    try:
        first_item = random.choices(first_items, weights=probabilities)[0]
    except:
        first_item = random.choice(first_items)
    
    selected_items.append(first_item)
    
    for category in sorted_categories[1:]:
        current_items = ClothingItem.objects.filter(user=user, category=category)
        
        if not current_items.exists():
            continue
        
        last_item = selected_items[-1]
        weights = []
        
        for candidate in current_items:
            compatibility = get_or_create_compatibility(user, last_item, candidate)
            weight = (candidate.rating + 1) * (compatibility + 2) / (candidate.times_shown + 1)
            weights.append(weight)
        
        if random.random() < 0.15 or sum(weights) == 0:
            selected_item = random.choice(current_items)
        else:
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            selected_item = random.choices(current_items, weights=normalized_weights)[0]
        
        selected_items.append(selected_item)
    
    return selected_items

def update_compatibility_scores(user, items, rating):
    """Обновляет оценки совместимости на основе рейтинга образа"""
    
    for i in range(len(items) - 1):
        item1 = items[i]
        item2 = items[i + 1]
        
        if item1.id > item2.id:
            item1, item2 = item2, item1
        
        compatibility = Compatibility.objects.get_or_create(
            user=user,
            item1=item1,
            item2=item2,
            defaults={'score': 0, 'times_evaluated': 0}
        )
        
        new_score = compatibility.score + (rating - 3) * 0.1
        new_score = max(-1.0, min(1.0, new_score))
        
        compatibility.score = new_score
        compatibility.times_evaluated += 1
        compatibility.save()

def get_recommendations(user):
    """Генерирует рекомендации для пользователя"""
    
    recommendations = []
    total_items = ClothingItem.objects.filter(user=user).count()
    
    if total_items < 5:
        recommendations.append(f"Добавьте больше вещей в гардероб (сейчас {total_items})")
    elif total_items < 10:
        recommendations.append("Добавьте ещё вещей для более разнообразных образов")
    
    categories = ClothingItem.CATEGORY_CHOICES
    for category_code, category_name in categories:
        count = ClothingItem.objects.filter(user=user, category=category_code).count()
        if count == 0:
            recommendations.append(f"Добавьте вещи категории '{category_name}'")
        elif count < 2 and total_items >= 10:
            recommendations.append(f"Мало вещей категории '{category_name}' ({count} шт.)")
    
    compat_count = Compatibility.objects.filter(user=user).count()
    if compat_count < 5:
        recommendations.append("Оцените несколько образов для обучения системы")
    
    return recommendations

def get_categories_with_items(user, categories):
    """Проверяет, есть ли вещи в выбранных категориях и возвращает только категории с вещами"""
    categories_with_items = []
    
    for category in categories:
        count = ClothingItem.objects.filter(
            user=user, 
            category=category
        ).count()
        if count > 0:
            categories_with_items.append(category)
    
    return categories_with_items

def validate_categories_for_generation(user, categories, min_categories=2):
    """Проверяет, достаточно ли категорий с вещами для генерации"""
    categories_with_items = get_categories_with_items(user, categories)
    
    if len(categories_with_items) < min_categories:
        return None, categories_with_items
    
    return categories_with_items, categories_with_items

def generate_and_save_outfit(request, categories):
    """Основная логика генерации и сохранения образа в сессии"""
    user = request.user
    valid_categories, _ = validate_categories_for_generation(user, categories)
    
    if not valid_categories:
        return None, "В выбранных категориях недостаточно вещей"
    
    generated_items = generate_outfit_algorithm(user, valid_categories)
    
    if not generated_items:
        return None, "Не удалось создать образ"
    
    request.session['generated_outfit'] = {
        'item_ids': [item.id for item in generated_items],
        'categories': valid_categories
    }
    
    request.session.pop('outfit_rated', None)
    request.session.pop('last_rating', None)
    
    return generated_items, None


def prepare_generation_context(request, form=None, generated_items=None, error_message=None):
    """Подготавливает контекст для рендеринга страницы генерации"""
    user = request.user
    recommendations = get_recommendations(user)
    has_generated_outfit = 'generated_outfit' in request.session
    outfit_rated = request.session.get('outfit_rated', False)
    last_rating = request.session.get('last_rating', None)
    saved_categories = request.session.get('selected_categories', [])
    
    if form is None:
        if saved_categories:
            form = GenerateOutfitForm(initial={'categories': saved_categories})
        else:
            form = GenerateOutfitForm()
    
    rating_form = None
    if has_generated_outfit and not outfit_rated:
        rating_form = RateOutfitForm()
    
    if generated_items is None and has_generated_outfit:
        outfit_data = request.session['generated_outfit']
        item_ids = outfit_data['item_ids']
        generated_items = ClothingItem.objects.filter(id__in=item_ids, user=user)
    
    context = {
        'form': form,
        'rating_form': rating_form,
        'generated': generated_items is not None,
        'generated_items': generated_items,
        'recommendations': recommendations,
        'outfit_rated': outfit_rated,
        'last_rating': last_rating,
        'actual_categories': request.session.get('selected_categories', []),
    }
    
    return context
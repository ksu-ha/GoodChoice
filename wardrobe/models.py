from django.db import models
from django.contrib.auth.models import User
from .utils import get_display_from_comma_separated


class ClothingItem(models.Model):
    """Модель вещи в гардеробе"""
    
    # Категории
    CATEGORY_CHOICES = [
        ('top', 'Верх'),
        ('bottom', 'Низ'),
        ('outer', 'Верхняя одежда'),
        ('dress', 'Костюм/Платье'),
        ('shoes', 'Обувь'),
        ('accessory', 'Аксессуары'),
    ]
    
    # Цвета
    COLOR_CHOICES = [
        ('red', 'Красный'),
        ('blue', 'Синий'),
        ('green', 'Зеленый'),
        ('black', 'Черный'),
        ('white', 'Белый'),
        ('pink', 'Розовый'),
        ('yellow', 'Желтый'),
        ('purple', 'Фиолетовый'),
        ('brown', 'Коричневый'),
        ('gray', 'Серый'),
        ('beige', 'Бежевый'),
        ('multicolor', 'Разноцветный'),
    ]
    
    # Сезоны
    SEASON_CHOICES = [
        ('winter', 'Зима'),
        ('spring', 'Весна'),
        ('summer', 'Лето'),
        ('autumn', 'Осень'),
    ]
    
    # Тип мероприятия
    OCCASION_CHOICES = [
        ('office', 'В офис'),
        ('home', 'Для дома'),
        ('walk', 'На прогулку'),
        ('party', 'На праздник'),
        ('any', 'Любой'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(upload_to='clothing/', verbose_name="Фото")
    description = models.TextField(verbose_name="Описание", blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, verbose_name="Цвет")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория")
    season = models.CharField(max_length=50, verbose_name="Сезон")
    occasion = models.CharField(max_length=100, verbose_name="Тип мероприятия")
    rating = models.IntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)], default=3, verbose_name="Личная оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    times_shown = models.IntegerField(default=0, verbose_name="Показов")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Вещь"
        verbose_name_plural = "Вещи"
        ordering = ['-created_at']

    def get_seasons_display(self):
        return get_display_from_comma_separated(self, 'season', self.SEASON_CHOICES)
    
    def get_occasion_display(self):
        return get_display_from_comma_separated(self, 'occasion', self.OCCASION_CHOICES)

class Outfit(models.Model):
    """Модель образа (комбинации вещей)"""
    
    OCCASION_CHOICES = ClothingItem.OCCASION_CHOICES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название образа")
    description = models.TextField(verbose_name="Описание", blank=True)
    items = models.ManyToManyField(ClothingItem, verbose_name="Вещи в образе")
    occasion = models.CharField(max_length=100, verbose_name="Тип мероприятия")
    rating = models.IntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)], default=3, verbose_name="Личная оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Образ"
        verbose_name_plural = "Образы"
        ordering = ['-created_at']

    def get_occasion_display(self):
        return get_display_from_comma_separated(self, 'occasion', self.OCCASION_CHOICES)
    
class Compatibility(models.Model):
    """Cовместимость вещей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    item1 = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='compatibility_as_item1')
    item2 = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='compatibility_as_item2')
    score = models.FloatField(default=0, verbose_name="Оценка совместимости")
    times_evaluated = models.IntegerField(default=0, verbose_name="Количество оценок")
    
    class Meta:
        unique_together = [['user', 'item1', 'item2']]
        verbose_name = "Совместимость"
        verbose_name_plural = "Совместимости"
    
    def __str__(self):
        return f"{self.item1} + {self.item2}: {self.score:.2f}"
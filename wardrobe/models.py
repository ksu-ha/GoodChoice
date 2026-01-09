from django.db import models
from django.contrib.auth.models import User

class ClothingItem(models.Model):
    """Модель вещи в гардеробе"""
    
    # Категории (как ты указала)
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
    
    # Сезоны (можно выбрать несколько - будем хранить как строку)
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
    
    # Сезон как CharField для хранения нескольких значений через запятую
    season = models.CharField(max_length=50, verbose_name="Сезон")
    
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES, default='any', verbose_name="Тип мероприятия")
    rating = models.IntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)], default=3, verbose_name="Личная оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Вещь"
        verbose_name_plural = "Вещи"
        ordering = ['-created_at']

class Outfit(models.Model):
    """Модель образа (комбинации вещей)"""
    
    OCCASION_CHOICES = ClothingItem.OCCASION_CHOICES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название образа")
    description = models.TextField(verbose_name="Описание", blank=True)
    items = models.ManyToManyField(ClothingItem, verbose_name="Вещи в образе")
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES, default='any', verbose_name="Тип мероприятия")
    rating = models.IntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)], default=3, verbose_name="Личная оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Образ"
        verbose_name_plural = "Образы"
        ordering = ['-created_at']
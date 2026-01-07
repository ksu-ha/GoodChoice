from django import forms
from .models import ClothingItem, Outfit

class ClothingItemForm(forms.ModelForm):
    """Форма для добавления/редактирования вещей"""
    
    season = forms.MultipleChoiceField(
        choices=ClothingItem.SEASON_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Сезон"
    )
    
    class Meta:
        model = ClothingItem
        fields = ['name', 'image', 'description', 'color', 'category', 'season', 'occasion', 'rating']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Красное платье'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание вещи...'
            }),
            'color': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'occasion': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'name': 'Название',
            'image': 'Фото',
            'description': 'Описание',
            'color': 'Цвет',
            'category': 'Категория',
            'occasion': 'Тип мероприятия',
            'rating': 'Личная оценка',
        }

class OutfitForm(forms.ModelForm):
    """Форма для создания образов"""
    
    class Meta:
        model = Outfit
        fields = ['name', 'description', 'items', 'occasion', 'rating']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Офисный образ на понедельник'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание образа...'
            }),
            'items': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 6
            }),
            'occasion': forms.Select(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'name': 'Название образа',
            'description': 'Описание',
            'items': 'Вещи в образе',
            'occasion': 'Тип мероприятия',
            'rating': 'Личная оценка',
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['items'].queryset = ClothingItem.objects.filter(user=user)
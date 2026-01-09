from django import forms
from .models import ClothingItem, Outfit
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class ClothingItemForm(forms.ModelForm):
    """Форма для добавления/редактирования вещей"""
    
    season = forms.MultipleChoiceField(
        choices=ClothingItem.SEASON_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Сезон"
    )
    
    class Meta:
        model = ClothingItem
        fields = ['name', 'image', 'description', 'color', 'category', 'season', 'occasion', 'rating', 'price']
        
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
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 2999.99',
                'step': '0.01'
            }),
        }
        
        labels = {
            'name': 'Название',
            'image': 'Фото',
            'description': 'Описание',
            'color': 'Цвет',
            'category': 'Категория',
            'occasion': 'Тип мероприятия',
            'rating': 'Личная оценка',
            'price': 'Цена (руб.)', 
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

class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации без email"""
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте логин'
            }),
        }
        
        labels = {
            'username': 'Логин',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ваш логин'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ваш пароль'
        })
        
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
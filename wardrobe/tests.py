from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import ClothingItem, Outfit, Compatibility
from .forms import ClothingItemForm, OutfitForm, CustomUserCreationForm, GenerateOutfitForm
from .utils import get_display_from_comma_separated


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.clothing_item = ClothingItem.objects.create(
            user=self.user,
            name='Test Shirt',
            description='A test shirt',
            color='blue',
            category='top',
            season='summer,spring',
            occasion='office,any',
            rating=4,
            price=1999.99
        )
        
        self.clothing_item2 = ClothingItem.objects.create(
            user=self.user,
            name='Test Pants',
            description='A test pants',
            color='black',
            category='bottom',
            season='summer,winter',
            occasion='office,walk',
            rating=5
        )

    def test_clothing_item_creation(self):
        """Тестирование создания вещи одежды"""
        self.assertEqual(self.clothing_item.name, 'Test Shirt')
        self.assertEqual(self.clothing_item.color, 'blue')
        self.assertEqual(self.clothing_item.category, 'top')
        self.assertEqual(self.clothing_item.rating, 4)
        self.assertEqual(self.clothing_item.price, 1999.99)
        self.assertTrue(self.clothing_item.created_at)

    def test_clothing_item_get_seasons_display(self):
        """Тестирование отображения сезонов"""
        seasons = self.clothing_item.get_seasons_display()
        self.assertIn('Лето', seasons)
        self.assertIn('Весна', seasons)

    def test_clothing_item_get_occasion_display(self):
        """Тестирование отображения типа мероприятия"""
        occasions = self.clothing_item.get_occasion_display()
        self.assertIn('В офис', occasions)
        self.assertIn('Любой', occasions)

    def test_outfit_creation(self):
        """Тестирование создания образа"""
        outfit = Outfit.objects.create(
            user=self.user,
            name='Test Outfit',
            description='A test outfit',
            occasion='office,walk',
            rating=4
        )
        outfit.items.add(self.clothing_item, self.clothing_item2)
        
        self.assertEqual(outfit.name, 'Test Outfit')
        self.assertEqual(outfit.items.count(), 2)
        self.assertEqual(outfit.rating, 4)
        self.assertTrue(outfit.created_at)

    def test_compatibility_creation(self):
        """Тестирование создания записи о совместимости"""
        compatibility = Compatibility.objects.create(
            user=self.user,
            item1=self.clothing_item,
            item2=self.clothing_item2,
            score=0.5,
            times_evaluated=3
        )
        
        self.assertEqual(compatibility.score, 0.5)
        self.assertEqual(compatibility.times_evaluated, 3)
        self.assertEqual(compatibility.item1, self.clothing_item)
        self.assertEqual(compatibility.item2, self.clothing_item2)


class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_clothing_item_form_missing_required_fields(self):
        """Тестирование формы без обязательных полей"""
        image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'test_image_content',
            content_type='image/jpeg'
        )
        
        # Не хватает названия
        form_data = {
            'name': '',
            'color': 'red',
            'category': 'top',
            'season': ['summer'],
            'occasion': ['office'],
            'rating': 5
        }
        
        form = ClothingItemForm(data=form_data, files={'image': image_file})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_clothing_item_form_missing_season(self):
        """Тестирование формы без сезона"""
        image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'test_image_content',
            content_type='image/jpeg'
        )
        
        # Нет сезона
        form_data = {
            'name': 'Test Item',
            'color': 'red',
            'category': 'top',
            'season': [],  # Пустой список
            'occasion': ['office'],
            'rating': 5
        }
        
        form = ClothingItemForm(data=form_data, files={'image': image_file})
        self.assertFalse(form.is_valid())
        self.assertIn('season', form.errors)

    def test_outfit_form_valid(self):
        """Тестирование валидной формы создания образа"""
        item1 = ClothingItem.objects.create(
            user=self.user,
            name='Test Item 1',
            color='blue',
            category='top',
            season='summer',
            occasion='office'
        )
        
        item2 = ClothingItem.objects.create(
            user=self.user,
            name='Test Item 2',
            color='black',
            category='bottom',
            season='summer',
            occasion='office'
        )
        
        form_data = {
            'name': 'New Outfit',
            'items': [item1.id, item2.id],
            'occasion': ['office'],
            'rating': 4
        }
        
        form = OutfitForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_user_creation_form_valid(self):
        """Тестирование валидной формы регистрации"""
        form_data = {
            'username': 'newuser',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_generate_outfit_form_valid(self):
        """Тестирование валидной формы генерации образа"""
        form_data = {
            'categories': ['top', 'bottom']
        }
        
        form = GenerateOutfitForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_generate_outfit_form_invalid(self):
        """Тестирование невалидной формы генерации образа"""
        form_data = {
            'categories': ['top']  # Только одна категория
        }
        
        form = GenerateOutfitForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('categories', form.errors)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.clothing_item1 = ClothingItem.objects.create(
            user=self.user,
            name='Test Item 1',
            color='blue',
            category='top',
            season='summer',
            occasion='office',
            rating=4
        )
        
        self.clothing_item2 = ClothingItem.objects.create(
            user=self.user,
            name='Test Item 2',
            color='black',
            category='bottom',
            season='summer',
            occasion='office',
            rating=4
        )

    def test_home_view_authenticated(self):
        """Тестирование главной страницы для авторизованного пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добро пожаловать')

    def test_add_clothing_item_view_get(self):
        """Тестирование GET запроса формы добавления вещи"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:add_item'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Добавить новую вещь')

    def test_wardrobe_list_view(self):
        """Тестирование страницы гардероба"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:wardrobe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Мой гардероб')

    def test_outfit_list_view(self):
        """Тестирование страницы списка образов"""
        outfit = Outfit.objects.create(
            user=self.user,
            name='Test Outfit',
            occasion='office',
            rating=4
        )
        outfit.items.add(self.clothing_item1)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:outfit_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Мои образы')

    def test_analytics_view_with_items(self):
        """Тестирование страницы аналитики с вещами"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Аналитика гардероба')

    def test_analytics_view_no_items(self):
        """Тестирование страницы аналитики без вещей"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        self.client.login(username='testuser2', password='testpass123')
        
        response = self.client.get(reverse('wardrobe:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Гардероб пуст')

    def test_register_view_get(self):
        """Тестирование GET запроса страницы регистрации"""
        response = self.client.get(reverse('wardrobe:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Регистрация')

    def test_register_view_post(self):
        """Тестирование POST запроса регистрации"""
        response = self.client.post(reverse('wardrobe:register'), {
            'username': 'newtestuser',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newtestuser').exists())

    def test_login_view_get(self):
        """Тестирование GET запроса страницы входа"""
        response = self.client.get(reverse('wardrobe:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вход')

    def test_login_view_post(self):
        """Тестирование POST запроса входа"""
        response = self.client.post(reverse('wardrobe:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """Тестирование выхода"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:logout'))
        self.assertEqual(response.status_code, 302)

    def test_delete_item_view(self):
        """Тестирование удаления вещи"""
        self.client.login(username='testuser', password='testpass123')
        item_id = self.clothing_item1.id
        
        response = self.client.post(
            reverse('wardrobe:delete_item', args=[item_id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClothingItem.objects.filter(id=item_id).exists())

    def test_generate_outfit_view_authenticated(self):
        """Тестирование страницы генерации образов"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('wardrobe:generate_outfit'))
        # У пользователя есть 2 вещи, должен вернуть 200
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Генератор образов')

    def test_generate_outfit_view_insufficient_items(self):
        """Тестирование генерации при недостаточном количестве вещей"""
        # Создаем пользователя с 0 вещей
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        self.client.login(username='testuser2', password='testpass123')
        
        response = self.client.get(reverse('wardrobe:generate_outfit'))
        self.assertEqual(response.status_code, 302)

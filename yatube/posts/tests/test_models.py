'''
TODO:
Спринт 5/16 → Тема 2/4: Тестирование Django → Урок 2/8
Дополнительное задание
Добавьте в поля модели Post атрибуты verbose_name
и help_text; протестируйте их.
'''

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group, please ignore',
            slug='test_slug',
            description='Test description, please ignore',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post, please ignore',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        self.assertEqual(str(post), self.post.text[:settings.POST_TEXT_SHORT])

    def test_group_model_have_correct_object_names(self):
        group = PostModelTest.group
        self.assertEqual(str(group), 'Test group, please ignore')

'''
TODO:
Спринт 5/16 → Тема 2/4: Тестирование Django → Урок 2/8
Дополнительное задание
Добавьте в поля модели Post атрибуты verbose_name
и help_text; протестируйте их.
'''

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        self.assertEqual(post.__str__(), self.post.text[:15])

    def test_group_model_have_correct_object_names(self):
        group = PostModelTest.group
        self.assertEqual(group.__str__(), 'Test group, please ignore')

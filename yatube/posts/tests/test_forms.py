from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()

class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title = 'Test group, please ignore',
            slug = 'Test_slug',
            description = 'Test description, please ignore',
        )
        cls.post = Post.objects.create(
            text = 'Test post, please ignore',
            author = cls.user,
            group = cls.group,
        )
        
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        '''Проверка формы, редирект, создание поста, автора'''
        post_count = Post.objects.count()
        form_data ={
            'text': 'text',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data = form_data,
            follow = True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author = self.user,
            text = form_data['text'],
            id = 2).exists()
            )

    def test_edit_post_form(self):
        '''Проверка формы редактирования поста'''
        post_count = Post.objects.count()
        form_data ={
            'text': 'Test edited_post, please ignore',
            'group': self.group.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data = form_data,
            follow = True,
        )
        # Пост существует
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Количество постов не изменилось
        self.assertEqual(Post.objects.count(), post_count)
        # Текст поста изменился
        self.assertTrue(Post.objects.filter(
            text = form_data['text']).exists()
            )
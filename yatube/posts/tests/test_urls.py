from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()


class UrlTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.post = Post.objects.create(
            text = 'Test text, please ignore',
            author = cls.user,
        )
        cls.group = Group.objects.create(
            title = 'Test title, please ignore',
            slug = 'test_slug',
            description = 'Test description, please ignore',
        )
    
    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls(self):
        '''Проверка на доступ гостем'''
        # TODO: сделать везде через reverse и args
        url_codes = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK, 
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, code in url_codes.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_url_to_template(self):
        '''Проверка соответствия url и template'''
        url_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            # reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            # 'posts/create_post.html',
            # f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for url, template in url_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit(self):
        '''Проверка на редактирование автором'''
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_non_author(self):
        '''Проверка на редактирование не автором'''
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, (f'/auth/login/?next=/posts/{self.post.id}/edit/'))

    def test_post_create_authorized(self):
        '''Проверка на создание поста авторизованным пользователем'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_non_authorized(self):
        '''Проверка на создание поста гостем'''
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertRedirects(response, (f'/auth/login/?next=/create/'))
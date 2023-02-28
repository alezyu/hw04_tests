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
            text='Test text, please ignore',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Test title, please ignore',
            slug='test_slug',
            description='Test description, please ignore',
        )
        # (url: template, guest_response, auth_response)
        cls.PUBLIC_URLS = {
            reverse('posts:index'): (
                'posts/index.html',
                HTTPStatus.OK,
                HTTPStatus.OK
            ),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}): (
                'posts/group_list.html',
                HTTPStatus.OK,
                HTTPStatus.OK
            ),
            reverse('posts:profile', kwargs={'username': cls.user}): (
                'posts/profile.html',
                HTTPStatus.OK,
                HTTPStatus.OK
            ),
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}): (
                'posts/post_detail.html',
                HTTPStatus.OK,
                HTTPStatus.OK
            ),
            '/unexisting_page/': (
                'core/404.html',
                HTTPStatus.NOT_FOUND,
                HTTPStatus.NOT_FOUND
            ),
        }
        cls.PRIVATE_URLS = {
            reverse('posts:post_create'): (
                'posts/create_post.html',
                '/auth/login/?next=/create/',
                HTTPStatus.OK
            ),
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}): (
                'posts/create_post.html',
                f'/auth/login/?next=/posts/{cls.post.id}/edit/',
                HTTPStatus.OK
            ),
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_pages(self):
        for url, test in self.PUBLIC_URLS.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                response_auth = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response_auth,
                    test[0],
                    'Неверный template страницы'
                )
                self.assertEqual(
                    response.status_code,
                    test[1],
                    'Неверный HTTPStatus на запрос гостя'
                )
                self.assertEqual(
                    response_auth.status_code,
                    test[2],
                    'Неверный HTTPStatus на запрос пользователя'
                )

    def test_private_pages(self):
        for url, test in self.PRIVATE_URLS.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                response_auth = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response_auth,
                    test[0],
                )
                # проверка на создание, редактирование гостем
                self.assertRedirects(response, test[1])

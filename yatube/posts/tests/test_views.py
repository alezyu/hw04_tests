# TODO переделать где можно через subTest
# TODO подобрать правильные assert'ы
from django import forms

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.user2 = User.objects.create_user(username='auth_user2')
        cls.group = Group.objects.create(
            title='Test title, please ignore',
            slug='test_slug',
            description='Test description, please ignore',
        )
        cls.group2 = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='Test text, please ignore',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_template_and_context(self):
        '''
        URL-адрес использует соответствующий шаблон,
        На каждой странице необходимый контекст
        '''
        # url: (template, test)
        url_tests = {
            reverse('posts:index'): ('posts/index.html', 'page_obj'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): ('posts/group_list.html', 'page_obj'),
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): ('posts/profile.html', 'page_obj'),
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): ('posts/post_detail.html', 'post'),
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): ('posts/create_post.html', 'form'),
            reverse('posts:post_create'): ('posts/create_post.html', 'form'),
        }
        for (
            url,
            test,
        ) in url_tests.items():
            # Проверка шаблонов
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, test[0])
            first_object = self.guest_client.get(url)
            if test[1] == 'post':
                first_object = first_object.context[test[1]]
            elif test[1] == 'page_obj':
                first_object = first_object.context[test[1]][0]
            # Проверка контекста страниц с формами
            elif test[1] == 'form':
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(
                            form_field,
                            expected,
                            f'Неверный контекст формы на странице {url}'
                        )
                continue
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
            }
            # Проверка контекста страниц
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_post_created_show_group_and_profile(self):
        '''
        Проверка на присутствие/отсутствие постов на странице
        соответствующей группы и пользователя, контекста групп/пользователя
        '''
        urls = {
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ):
                (
                    1,
                    list(Post.objects.filter(group=self.group.id)),
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ):
                (
                    1,
                    list(Post.objects.filter(author=self.user)),
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group2.slug}
            ):
                (
                    0,
                    [],
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user2.username}
            ):
                (
                    0,
                    [],
            ),
        }
        for url, test in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), test[0])
                self.assertEqual(
                    list(response.context.get('page_obj')), test[1]
                )


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # POSTS_ON_SECOND_PAGE in range 1..settings.POSTS_PER_PAGE
        cls.POSTS_ON_SECOND_PAGE = 7
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Test title, please ignore',
            slug='test_slug',
            description='Test description, please ignore',
        )
        posts = (
            Post(
                text='Test text, please ignore',
                group=cls.group,
                author=cls.user,
            )
            for i in range(settings.POSTS_PER_PAGE + cls.POSTS_ON_SECOND_PAGE)
        )
        Post.objects.bulk_create(posts)

        cls.URLS = {
            reverse('posts:index'): settings.POSTS_PER_PAGE,
            reverse('posts:index') + '?page=2': cls.POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): settings.POSTS_PER_PAGE,
            reverse('posts:group_list', kwargs={'slug': cls.group.slug})
            + '?page=2': cls.POSTS_ON_SECOND_PAGE,
            reverse(
                'posts:profile', kwargs={'username': cls.user}
            ): settings.POSTS_PER_PAGE,
            reverse('posts:profile', kwargs={'username': cls.user})
            + '?page=2': cls.POSTS_ON_SECOND_PAGE,
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_all(self):
        '''Проверка пагинатора'''
        for url, posts_count in self.URLS.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context.get('page_obj')), posts_count
                )

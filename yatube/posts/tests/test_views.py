# TODO переделать где можно через subTest
# TODO подобрать правильные assert'ы
from django import forms

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

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        url_to_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
        }
        for reverse_name, template,  in url_to_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        '''Проверка контекста posts:index'''
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.author.username, self.user.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.title, self.group.title)

    def test_group_list_show_correct_context(self):
        '''Проверка контекста posts:group_list'''
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        ))
        expected = list(Post.objects.filter(group=self.group.id))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_profile_show_correct_context(self):
        '''Проверка контекста posts:profile'''
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        expected = list(Post.objects.filter(author=self.user))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_post_detail_show_correct_context(self):
        '''Проверка контекста post_detail'''
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        post_obj = response.context.get('post')
        self.assertEqual(post_obj, self.post)

    form_fields = {
        'text': forms.fields.CharField,
        'group': forms.fields.ChoiceField,
    }

    def test_create_post_show_correct_context(self):
        '''Проверка контекста создание поста posts:post_create'''
        response = self.authorized_client.get(reverse(
            'posts:post_create',
            kwargs={})
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_edit_post_show_correct_context(self):
        '''Проверка контекста редактирование поста posts:post_create'''
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        ))
        self.assertTrue(response.context.get('is_edit'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_post_created_not_show_group_profile(self):
        '''Проверка на отсутстствие постов где их не должно быть'''
        urls = (
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}),
            reverse('posts:profile', kwargs={'username': self.user2.username})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 0)

    def test_post_created_show_group_and_profile(self):
        '''
        Проверка на присутствие постов на странице
        соответствующей группы и пользователя
        '''
        urls = (
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 1)


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Test title, please ignore',
            slug='test_slug',
            description='Test description, please ignore',
        )
        posts = (Post(
            text='Test text, please ignore',
            group=cls.group,
            author=cls.user,
        ) for i in range(13))
        Post.objects.bulk_create(posts)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_index_page(self):
        '''Проверяем что выведено 10 постов на главной'''
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context.get('page_obj')), 10
        )

    def test_paginator_index_page_two(self):
        '''Проверяем что выведено 3 поста на второй странице'''
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 3)

    def test_paginator_group_page(self):
        '''Проверяем количество постов на странице группы'''
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        ))
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_paginator_group_page_two(self):
        '''Проверяем количество постов на второй странице группы'''
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        ) + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 3)

    def test_paginator_profile_page(self):
        '''
        Проверяем количество постов пользователя
        в профиле на первой странице
        '''
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ))
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_paginator_profile_page_two(self):
        '''
        Проверяем количество постов пользователя в профиле на второй странице
        '''
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user}
        ) + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 3)

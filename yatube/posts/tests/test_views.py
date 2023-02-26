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
        cls.user = User.objects.create_user(username="auth_user")
        cls.user2 = User.objects.create_user(username="auth_user2")
        cls.group = Group.objects.create(
            title="Test title, please ignore",
            slug="test_slug",
            description="Test description, please ignore",
        )
        cls.group2 = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )
        cls.post = Post.objects.create(
            text="Test text, please ignore",
            author=cls.user,
            group=cls.group,
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # url: (template, )
        url_to_template = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.user}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for (
            url,
            template,
        ) in url_to_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_show_correct_context(self):
        """Проверка на контекст"""
        url = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for url, context in url.items():
            first_object = self.guest_client.get(url)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_create_post_show_correct_context(self):
        """
        Проверка контекста редактирование поста
        posts:post_create и posts:edit
        """
        urls = [
            reverse("posts:post_create"),
            reverse("posts:post_edit", args=[self.post.pk]),
        ]
        for url in urls:
            response = self.authorized_client.get(url)
            form_fields = {
                "text": forms.fields.CharField,
                "group": forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context["form"].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_created_show_group_and_profile(self):
        """
        Проверка на присутствие/отсутствие постов на странице
        соответствующей группы и пользователя, контекста групп/пользователя
        """
        urls = {
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug}
            ):
                (
                    1,
                    list(Post.objects.filter(group=self.group.id)),
            ),
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username}
            ):
                (
                    1,
                    list(Post.objects.filter(author=self.user)),
            ),
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group2.slug}
            ):
                (
                    0,
                    [],
            ),
            reverse(
                "posts:profile",
                kwargs={"username": self.user2.username}
            ):
                (
                    0,
                    [],
            ),
        }
        for url, test in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get("page_obj")
                self.assertEqual(len(page_obj), test[0])
                self.assertEqual(
                    list(response.context.get("page_obj")), test[1]
                )


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # POSTS_ON_SECOND_PAGE in range 1..settings.POSTS_PER_PAGE
        cls.POSTS_ON_SECOND_PAGE = 7
        cls.user = User.objects.create_user(username="auth_user")
        cls.group = Group.objects.create(
            title="Test title, please ignore",
            slug="test_slug",
            description="Test description, please ignore",
        )
        posts = (
            Post(
                text="Test text, please ignore",
                group=cls.group,
                author=cls.user,
            )
            for i in range(settings.POSTS_PER_PAGE + cls.POSTS_ON_SECOND_PAGE)
        )
        Post.objects.bulk_create(posts)

        cls.URLS = {
            reverse("posts:index"): settings.POSTS_PER_PAGE,
            reverse("posts:index") + "?page=2": cls.POSTS_ON_SECOND_PAGE,
            reverse(
                "posts:group_list", kwargs={"slug": cls.group.slug}
            ): settings.POSTS_PER_PAGE,
            reverse("posts:group_list", kwargs={"slug": cls.group.slug})
            + "?page=2": cls.POSTS_ON_SECOND_PAGE,
            reverse(
                "posts:profile", kwargs={"username": cls.user}
            ): settings.POSTS_PER_PAGE,
            reverse("posts:profile", kwargs={"username": cls.user})
            + "?page=2": cls.POSTS_ON_SECOND_PAGE,
        }

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_all(self):
        """Проверка пагинатора"""
        for url, posts_count in self.URLS.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context.get("page_obj")), posts_count
                )

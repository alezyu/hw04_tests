import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Test group, please ignore',
            slug='Test_slug',
            description='Test description, please ignore',
        )
        cls.group2 = Group.objects.create(
            title='Test group2, please ignore',
            slug='Test_slug2',
            description='Test description2, please ignore',
        )
        cls.post = Post.objects.create(
            text='Test post, please ignore',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_form(self):
        '''Проверка формы, редирект, создание поста, автора'''
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Lorem Ipsum',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text=form_data['text'],
            image='posts/small.gif',
        ).exists(),
            f'Ошибка при создании формы: author={self.user}, '
            f'text={form_data["text"]} '
            f'image={form_data["image"]}',
        )

    def test_edit_post_form(self):
        '''Проверка формы редактирования поста'''
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test edited_post, please ignore',
            'group': self.group2.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        # Пост существует
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Количество постов не изменилось
        self.assertEqual(Post.objects.count(), post_count)
        # Текст поста изменился
        self.assertTrue(Post.objects.filter(
            text=form_data['text']).exists(),
        )
        # Группа изменилась
        self.assertTrue(Post.objects.filter(
            group=form_data['group']).exists(),
        )

    def test_auth_create_comment(self):
        '''Авторизованный пользователь может комментировать посты'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Test comment, please ignore',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        new_comments_count = Comment.objects.count() - comments_count
        self.assertEqual(new_comments_count,
                         1,
                         'Авторизованный пользователь не может'
                         ' добавлять комментарии',
                         )
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
        ).exists(),
            'Не добавился текст комментария из формы',
        )
        self.assertTrue(Comment.objects.filter(
            post=self.post,
        ).exists(),
            'Не добавился комментарий к нужному посту',
        )
        self.assertTrue(Comment.objects.filter(
            author=self.user,
        ).exists(),
            'Комментарий добавляется не от того пользователя',
        )

    def test_guest_create_comment(self):
        '''Гости не могут комментировать посты.'''
        comments_count = Comment.objects.count()
        form_data = {
            "text": "Test guest comment, please ignore",
        }
        self.guest_client.post(
            reverse("posts:add_comment", kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count,
            'Гость не должен добавлять комментарий',
        )

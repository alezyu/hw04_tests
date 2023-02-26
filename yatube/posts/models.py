from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='сообщество')
    slug = models.SlugField(
        max_length=40,
        unique=True,
        null=False,
    )
    description = models.TextField(
        max_length=200,
        verbose_name='описание сообщества',
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='публикация')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='сообщество',
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.text[:settings.POST_TEXT_SHORT]

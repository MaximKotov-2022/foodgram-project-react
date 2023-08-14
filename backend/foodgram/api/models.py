from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from foodgram.settings import MAX_LENGTH_EMAIL, MAX_LENGTH_PERSONAL_DATA

from .validators import validate_username


class User(AbstractUser):
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
    )
    username = models.CharField(
        max_length=MAX_LENGTH_PERSONAL_DATA,
        blank=True,
        unique=True,
        validators=[validate_username]
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_PERSONAL_DATA,
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_PERSONAL_DATA,
    )
    password = models.CharField(
        max_length=MAX_LENGTH_PERSONAL_DATA,
    )
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_users',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_users',
        blank=True
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Вы не можете подписаться на себя.')

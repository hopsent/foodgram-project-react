from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    """Customize :model:'users.User'."""


    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]

    objects = UserManager()

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subscription(models.Model):
    """
    Store subsription, a relationship between
    :model:'users.User' as authorised user and
    :model:'users.User' as :model:'recipes.Recipe'
    instance author.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriber",
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribing",
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author', ],
                name='unique_subscription'
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'Подписка {self.user} на {self.author}.'

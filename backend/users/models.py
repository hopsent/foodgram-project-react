from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Customize :model:'users.User'."""

    email = models.EmailField(blank=False)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)


    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.username


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
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribing",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author', ],
                name='unique_subscription'
            ), 
        ]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}.'

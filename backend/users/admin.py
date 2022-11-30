from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription


class UserAdminExtended(UserAdmin):
    """
    To filter users against email and username.
    """

    list_filter = UserAdmin.list_filter + ('email', 'username',)


admin.site.register(Subscription)
admin.site.register(User, UserAdminExtended)

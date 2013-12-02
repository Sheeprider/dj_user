# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from user.forms import BaseUserEditionForm


class BaseUserForm(BaseUserEditionForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'is_active', 'is_staff', 'created_at', 'slug', 'name', '_fb_token', '_fb_id', '_avatar', '_small_avatar',)


class BaseUserAdmin(admin.ModelAdmin):
    fieldsets = [
        (_('Profil'), {'fields': ['email']}),
        (_('Status'), {'fields': ['is_active', 'is_staff']}),
        (_('Technical data'), {'fields': ['slug', 'created_at', 'last_login'], 'classes': ['collapse']}),
    ]
    search_fields = ('name', 'email')
    list_display = ('name', 'email', 'created_at', 'last_login')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'last_login', '_fb_id', '_fb_token')
    prepopulated_fields = {'slug': ('name',)}

    form = BaseUserForm

    def queryset(self, request):
        """ Only show administrators """
        qs = super(BaseUserAdmin, self).queryset(request)
        return qs.filter(is_superuser=True)

admin.site.register(get_user_model(), BaseUserAdmin)

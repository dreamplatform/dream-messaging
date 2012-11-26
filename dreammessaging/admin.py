# -*- coding: utf-8 -*-

from django.contrib import admin
from dreammessaging.models import Message


class MessageAdmin(admin.ModelAdmin):
  list_display = ('timestamp', 'msg_id', 'from_user', 'group', 'role')

admin.site.register(Message, MessageAdmin)

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


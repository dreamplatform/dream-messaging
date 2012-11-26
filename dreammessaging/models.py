# -*- coding: utf-8 -*-
"""Models for dream messaging"""

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Q
from hutils.managers import QuerySetManager

MESSAGE_TYPES = (
  (1, _('Group message')),
  (2, _('Announcement message')),
)


class Message(models.Model):
  timestamp = models.DateTimeField(auto_now_add=True, blank=False, null=False)
  msg_id = models.CharField(max_length=50, blank=True)
  from_user = models.ForeignKey('dreamsso.User', related_name='messages_from', null=True)
  to_user = models.ManyToManyField('dreamsso.User', related_name='messages_to')
  group = models.ForeignKey('dreamsso.Group', related_name='messages', blank=True, null=True)
  role = models.ForeignKey('dreamsso.Role', related_name='messages', blank=True, null=True)
  body = models.TextField(blank=True)

  objects = QuerySetManager()

  class QuerySet(models.query.QuerySet):
    def for_user(self, user):
      return self.filter(Q(from_user=user) | Q(to_user=user) | Q(group__in=user.user_groups.all) | Q(role__in=user.roles.all))

  class Meta:
    ordering = ['-timestamp', 'msg_id']

  def __unicode__(self):
    return u"%s - %s" % (self.timestamp, self.msg_id)


# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2

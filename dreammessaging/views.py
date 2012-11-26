
# -*- coding: utf-8 -*-

import logging
from itertools import groupby
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from dreamsso.models import Group, Role
from dreammessaging.models import Message
from dreammessaging.forms import MessageForm, MessageListFilterForm, RecipientForm
from dreammessaging.xmpp import send_message
from dreammessaging.utils import AjaxSnippetTemplateResponseMixin

LOG = logging.getLogger(__name__)


class MyMessagesView(ListView):
  model = Message
  allow_empty = True
  template_name = 'dreammessaging/my_messages.html'

  def get_queryset(self):
    user = self.request.user
    return self.model.objects.for_user(user)[:5]


class MessageView(AjaxSnippetTemplateResponseMixin, DetailView):
  model = Message

  def get_queryset(self):
    user = self.request.user
    qs = self.model.objects.for_user(user)
    return qs


class MessageListView(ListView):
  model = Message
  allow_empty = True
  paginate_by = 25

  def get_context_data(self, **kwargs):
    context = super(MessageListView, self).get_context_data(**kwargs)
    context['now'] = timezone.now()
    context['filter_form'] = self.filter_form

    def extract_date(obj):
      return obj.timestamp.date()

    data = []
    for k, g in groupby(context['object_list'], extract_date):
      d = {'date': k, 'objects': list(g)}
      data.append(d)

    context['object_list_group_by_date'] = data
    return context

  def get_queryset(self):
    user = self.request.user
    qs = self.model.objects.for_user(user)
    if 'query' in self.filters:
      # TODO Implement free text search
      qs = qs.filter(body__icontains=self.filters['query'])
    # TODO Message type filtering
    if 'group' in self.filters and self.filters['group']:
      qs = qs.filter(group=self.filters['group'])
    if 'role' in self.filters and self.filters['role']:
      qs = qs.filter(role=self.filters['role'])
    if 'begin' in self.filters and self.filters['begin']:
      qs = qs.filter(timestamp=self.filters['begin'])
    return qs

  def get(self, request, *args, **kwargs):
    self.filters = {}
    self.filter_form = MessageListFilterForm(data=request.GET, user=request.user)
    if self.filter_form.is_valid():
      self.filters = self.filter_form.cleaned_data
    return super(MessageListView, self).get(request, *args, **kwargs)


class MessageListLinearView(ListView):
  model = Message
  paginate_by = 25
  template_name = 'dreammessaging/message_list_linear.html'
  kind = None

  def get(self, request, *args, **kwargs):
    self.room_id = kwargs.get('pk', None)
    return super(MessageListLinearView, self).get(request, *args, **kwargs)

  def get_queryset(self):
    qs = self.model.objects.none()
    if 'pk' in self.kwargs:
      user = self.request.user
      qs = self.model.objects.for_user(user)
      qs = qs.filter(**{'%s__pk' % self.kind: self.kwargs['pk']})
    return qs


class MessageListRoleView(MessageListLinearView):
  kind = 'role'

  def get(self, request, *args, **kwargs):
    if kwargs['pk'] is None:
      try:
        pk = self.request.user.roles.order_by('title')[0].id
        return redirect(reverse_lazy('dreammessaging.list_role', kwargs={'pk': pk}))
      except IndexError:
        pass
    return super(MessageListRoleView, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(MessageListRoleView, self).get_context_data(**kwargs)
    context['url_kind'] = 'dreammessaging.list_role'
    context['room'] = self.request.user.roles.get(pk=self.room_id)
    context['room_list'] = self.request.user.roles.all().order_by('organisation__title', 'title')
    return context


class MessageListGroupView(MessageListLinearView):
  kind = 'group'

  def get(self, request, *args, **kwargs):
    if kwargs['pk'] is None:
      try:
        pk = self.request.user.user_groups.order_by('title')[0].id
        return redirect(reverse_lazy('dreammessaging.list_group', kwargs={'pk': pk}))
      except IndexError:
        pass
    return super(MessageListGroupView, self).get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(MessageListGroupView, self).get_context_data(**kwargs)
    context['url_kind'] = 'dreammessaging.list_group'
    context['room'] = self.request.user.user_groups.get(pk=self.room_id)
    context['room_list'] = self.request.user.user_groups.all().order_by('organisation__title', 'title')
    return context


class RecipientView(FormView):
  template_name = 'dreammessaging/message_to.html'
  form_class = RecipientForm
  success_url = reverse_lazy('dreammessaging.to')

  def get_initial(self):
    initial = super(RecipientView, self).get_initial()
    group = self.request.session.get('dreammessaging_to_group', None)
    if group:
      initial['group'] = group
    return initial

  def get_form_kwargs(self):
    kwargs = super(RecipientView, self).get_form_kwargs()
    kwargs['user'] = self.request.user
    return kwargs

  def get_context_data(self, **kwargs):
    kwargs['has_many_organisations'] = self.request.user.organisations.count() > 1
    return super(RecipientView, self).get_context_data(**kwargs)

  def form_valid(self, form):
    self.request.session['dreammessaging_to_group'] = form.cleaned_data['group'].id
    return redirect(reverse_lazy('dreammessaging.send'))


class SendMessageView(FormView):
  template_name = 'dreammessaging/message_send.html'
  form_class = MessageForm
  success_url = reverse_lazy('dreammessaging.send')

  def get_form_kwargs(self):
    kwargs = super(SendMessageView, self).get_form_kwargs()
    kwargs['user'] = self.request.user
    return kwargs

  def get_context_data(self, **kwargs):
    try:
      group = getattr(self, 'group', None)
      kwargs['group'] = self.request.user.user_groups.get(id=group)
    except Group.DoesNotExist:
      pass
    return super(SendMessageView, self).get_context_data(**kwargs)

  def get_initial(self):
    initial = super(SendMessageView, self).get_initial()
    group = self.request.session.get('dreammessaging_to_group', None)
    if group:
      initial['group'] = group
    return initial

  def form_valid(self, form):
    user = self.request.user
    group = form.cleaned_data['group']
    role = form.cleaned_data['role']
    message = form.cleaned_data['message']

    if 'send' in self.request.POST:
      jid = None
      if group:
        jid = 'group-%s' % group.id
      if role:
        jid = 'role-%s' % role.id

      if jid:
        send_message(user, jid, message)

    del self.request.session['dreammessaging_to_group']
    return redirect(reverse_lazy('dreammessaging.success'))

  def get(self, request, *args, **kwargs):
    self.group = self.request.session.get('dreammessaging_to_group', None)
    if not self.group:
      return redirect(reverse_lazy('dreammessaging.to'))
    return super(SendMessageView, self).get(request, *args, **kwargs)

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


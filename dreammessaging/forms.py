
# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from dreamsso.models import Group, Role
from dreammessaging.models import MESSAGE_TYPES


class MessageListFilterForm(forms.Form):
  # TODO Message type filtering
  #message_type = forms.TypedChoiceField(choices=MESSAGE_TYPES, coerce=int, required=False)
  group = forms.ModelChoiceField(queryset=Group.objects.none(), required=False)
  role = forms.ModelChoiceField(queryset=Role.objects.none(), required=False)
  query = forms.CharField(required=False)
  begin = forms.DateField(required=False)
  page = forms.IntegerField(required=False)

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user')
    super(MessageListFilterForm, self).__init__(*args, **kwargs)
    self.fields['group'].queryset = self.user.user_groups.all()
    self.fields['role'].queryset = self.user.roles.all()
    self.fields['query'].widget.attrs['placeholder'] = _('Search query')
    self.fields['page'].widget.hidden = True


class RecipientForm(forms.Form):
  group = forms.ChoiceField(widget=forms.RadioSelect, label=_(u'Recipient group'))

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user')
    super(RecipientForm, self).__init__(*args, **kwargs)
    groups = self.user.user_groups.order_by('organisation__id', 'title')
    self.fields['group'].choices = [(g.id, g.title) for g in groups]

  def clean_group(self):
    if not self.cleaned_data['group']:
      return None
    try:
      return self.user.user_groups.get(id=self.cleaned_data['group'])
    except Group.DoesNotExist:
      raise forms.ValidationError(_('Group does not exist'))


class MessageForm(forms.Form):
  group = forms.IntegerField(widget=forms.HiddenInput, required=False, label=_(u'Recipient group'))
  role = forms.IntegerField(widget=forms.HiddenInput, required=False, label=_(u'Recipient role'))
  message = forms.CharField(widget=forms.Textarea, label=_(u'Message to be sent'))

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user')
    return super(MessageForm, self).__init__(*args, **kwargs)

  def clean_group(self):
    if not self.cleaned_data['group']:
      return None
    try:
      return self.user.user_groups.get(id=self.cleaned_data['group'])
    except Group.DoesNotExist:
      raise forms.ValidationError(_('Group does not exist'))

  def clean_role(self):
    if not self.cleaned_data['role']:
      return None
    try:
      return self.user.roles.get(id=self.cleaned_data['role'])
    except Role.DoesNotExist:
      raise forms.ValidationError(_('Role does not exist'))


# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


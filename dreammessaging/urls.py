
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from dreammessaging.views import MyMessagesView
from dreammessaging.views import MessageView
from dreammessaging.views import MessageListView, MessageListRoleView, MessageListGroupView
from dreammessaging.views import SendMessageView, RecipientView


urlpatterns = patterns('',
  url(r'^$', login_required(MessageListView.as_view()), name='dreammessaging.list'),
  url(r'^mine/$', login_required(MyMessagesView.as_view()), name='dreammessaging.mine'),
  url(r'^conversation/r/(?P<pk>\d+)?/?$', login_required(MessageListRoleView.as_view()), name='dreammessaging.list_role'),
  url(r'^conversation/g/(?P<pk>\d+)?/?$', login_required(MessageListGroupView.as_view()), name='dreammessaging.list_group'),
  url(r'^message/(?P<pk>\d+)/$', login_required(MessageView.as_view()), name='dreammessaging.message'),
  url(r'^new/send/$', login_required(SendMessageView.as_view()), name='dreammessaging.send'),
  url(r'^new/to/$', login_required(RecipientView.as_view()), name='dreammessaging.to'),
  url(r'^new/sent/$', login_required(TemplateView.as_view(template_name='dreammessaging/message_success.html')), name='dreammessaging.success'),
)


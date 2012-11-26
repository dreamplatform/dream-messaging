
# -*- encoding: utf-8 -*-

import logging
import datetime
import sleekxmpp

from django.core.management.base import BaseCommand
from django.conf import settings as s
from django.core.cache import cache

from dreammessaging.models import Message
from dreamsso.models import User, Group, Role

LOG = logging.getLogger(__name__)

#TODO: Make sure changes in database will invalidate our cache (use xmpp pubsub)


def jid_to_user(jid):
  """jid can be in form user@msg.dreamschool.fi/Home"""
  username = jid.split('@')[0]
  user_obj = cache.get('user_%s' % username, None)
  if not user_obj:
    user_obj = User.objects.get(username=username)
    cache.set('user_%s' % username, user_obj)
  LOG.debug('returning user object %s for jid %s' % (user_obj, jid))
  return user_obj


def jid_to_group(jid):
  """Name of muc room needs to be in format group-<groupid>@conference.msg.dreamschool.fi/<user>"""
  group_id = int(jid.split('@')[0].split('-')[1])
  group_obj = cache.get('group_%s' % group_id, None)
  if not group_obj:
    group_obj = Group.objects.get(pk=group_id)
    cache.set('group_%s' % group_id, group_obj)
  LOG.debug('returning group object %s for jid %s' % (group_obj, jid))
  return group_obj


def jid_to_role(jid):
  """Name of muc room needs to be in format role-<roleid>@conference.msg.dreamschool.fi/<user>"""
  role_id = int(jid.split('@')[0].split('-')[1])
  role_obj = cache.get('role_%s' % role_id, None)
  if not role_obj:
    role_obj = Role.objects.get(pk=role_id)
    cache.set('role_%s' % role_id, role_obj)
  LOG.debug('returning role object %s for jid %s' % (role_obj, jid))
  return role_obj


def msg_to_obj(msg):
  """Creates message object"""
  msg_obj = Message()
  msg_obj.from_user = jid_to_user(unicode(msg['from']))
  msg_obj.body = unicode(msg['body'])
  msg_obj.msg_id = msg.get('id', None)
  msg_obj.save()
  msg_obj.to_user.add(jid_to_user(unicode(msg['to'])))
  LOG.debug('Created message object %s from msg %s' % (repr(msg_obj), repr(msg)))
  return msg_obj


def muc_msg_to_obj(msg):
  time_range = datetime.datetime.now() - datetime.timedelta(minutes=15)
  LOG.debug("msg[from] = %s" % (unicode(msg['from'])))
  LOG.debug("msg[to] = %s" % (unicode(msg['to'])))
  #FIXME: Stacktrace if filtering returns more than one Message
  LOG.debug('get_or_create: msg_id=%s, body=%s, timestamp_gte=%s' % (unicode(msg['id']), unicode(msg['body']), repr(time_range)))
  msg_obj, created = Message.objects.get_or_create(msg_id=unicode(msg['id']), body=unicode(msg['body']), timestamp__gte=time_range)
  if created:
    LOG.debug('Created new message object with id %s' % (msg_obj.pk))
  else:
    LOG.debug('Adding information to existing message object %s' % (msg_obj.pk))
  if unicode(msg['from']).startswith(u'role-') or unicode(msg['from']).startswith(u'group-'):
    # this message is from chatroom to users
    LOG.debug('processing message from chatroom to users')
    if unicode(msg['from']).startswith(u'group-'):
      LOG.debug("from field starts with 'group-' (%s)" % unicode(msg['from']))
      g_obj = jid_to_group(unicode(msg['from']))
      LOG.debug('Group obj %s, type %s' % (g_obj, type(g_obj)))
      msg_obj.group = g_obj
    elif unicode(msg['from']).startswith(u'role-'):
      LOG.debug("from field starts with 'role-' (%s)" % unicode(msg['from']))
      msg_obj.role = jid_to_role(unicode(msg['from']))
    LOG.debug('saving message %s' % msg_obj)
    msg_obj.save()
    to_user = jid_to_user(unicode(msg['to']))
    if to_user != msg_obj.from_user:
      LOG.debug('Adding %s to the recipient field' % (unicode(msg['to'])))
      msg_obj.to_user.add(jid_to_user(unicode(msg['to'])))
  else:
    # this message is from user to chatroom
    LOG.debug('processing message from a user to chatroom')
    LOG.debug('setting from-field to %s' % unicode(msg['from']))
    msg_obj.from_user = jid_to_user(unicode(msg['from']))
    msg_obj.save()
    LOG.debug('Saved message %s with pk %s' % (msg_obj, msg_obj.pk))
  LOG.debug('Created message object (id=%s) %s from msg %s' % (msg_obj.pk, repr(msg_obj), repr(msg)))
  return msg_obj


class XMPPLogger(sleekxmpp.componentxmpp.ComponentXMPP):

  previous_message = None  # For dropping duplicates

  def __init__(self, jid, password, *args, **kwargs):
    sleekxmpp.componentxmpp.ComponentXMPP.__init__(self, jid, password, *args, **kwargs)
    self.add_event_handler('message', self.message)
    self.use_ipv6 = False

  def message(self, msg):
    if msg == self.previous_message:
      #FIXME: What happens if messages don't arrive one after another
      LOG.debug('Compared msg %s to %s. Seems to be the same. Dropping duplicate' %
                (repr(msg), repr(msg)))
      return

    LOG.debug('Received message %s' % (repr(msg)), extra={'data': msg['type']})

    try:
      if msg['type'] == 'groupchat':
        LOG.debug("message is of type 'groupchat'. Passing it to method muc_msg_to_obj")
        muc_obj = muc_msg_to_obj(msg)
        LOG.debug('Message %s saved to db' % (repr(muc_obj)))
      else:
        LOG.debug("message is of type '%s'. Passing it to method msg_to_obj" % (unicode(msg['type'])))
        msg_obj = msg_to_obj(msg)
        LOG.debug('Message %s saved to db' % (repr(msg_obj)))
      self.previous_message = msg
    except Exception:
      LOG.exception('Could not save message %s to database' % repr(msg))

  def incoming_filter(self, xml):
    xml = super(XMPPLogger, self).incoming_filter(xml)
    if xml.tag.startswith('{jabber:component:accept}route'):
      # strip <route>realstuff</route>. This is how mod_server_log wraps it
      xml = xml.getchildren()[0]
    return xml


class Command(BaseCommand):
  help = 'Logs XMPP messages to database'

  def handle(self, *args, **options):
    LOG.debug('Trying to connect with parameters pass=%s, host=%s, port=%s' % (s.XMPP_LOG_PASS, s.XMPP_HOST, s.XMPP_LOG_PORT))
    xmpp = XMPPLogger('', s.XMPP_LOG_PASS, host=s.XMPP_HOST, port=s.XMPP_LOG_PORT)

    LOG.info('Connecting to XMPP service...')
    if xmpp.connect(use_ssl=False, use_tls=False):
      LOG.info('Connected to xmpp server. Waiting for messages to log into the database')
      xmpp.process(block=True)
    else:
      LOG.error('Could not connect to %s:%s' % (s.XMPP_HOST, s.XMPP_LOG_PORT))


# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


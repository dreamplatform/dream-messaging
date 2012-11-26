
# -*- coding: utf-8 -*-
"""MucBot (Kurre) creates muc chat room at xmpp-server for each role and group"""

import logging
import sleekxmpp
from sleekxmpp.exceptions import IqTimeout, IqError
from xml.etree import cElementTree as ET
from django.core.management.base import BaseCommand
from django.conf import settings
from dreamsso.models import Group, Role, User

LOG = logging.getLogger(__name__)


class MUCBot(sleekxmpp.ClientXMPP):
  def __init__(self, jid, password, nick):
    sleekxmpp.ClientXMPP.__init__(self, jid, password)
    self.use_ipv6 = False

    self.rooms = {}
    self.nick = nick

    self.add_event_handler('session_start', self.start)
    self.add_event_handler('message', self.message)
    self.add_event_handler('disconnected', self._handle_disconnect)

  def user_joined_muc(self, pr):
    """ Process 'muc::%s::got_online' event
    """
    entry = pr['muc'].getStanzaValues()
    room = unicode(entry['room'])
    jid = unicode(entry['jid'])
    if not jid:
      return

    if jid.startswith(settings.XMPP_MUC_USER):
      # This is me! And I'm the admin.
      self.plugin['xep_0045'].setAffiliation(room, jid=settings.XMPP_MUC_USER, affiliation='admin')
      LOG.debug('Setting %s as admin to room %s' % (settings.XMPP_MUC_USER, room))
      return

    username = jid.split('@')[0]
    try:
      user_obj = User.objects.get(username=username)
    except:
      # This should never happen as only authenticated users can connect to the server
      # Ban everyone who got here.
      LOG.error('User %s does not exists in userdb' % username)
      self.plugin['xep_0045'].setAffiliation(room, jid=jid, affiliation='outcast')
      LOG.info('banned user %s from room %s' % (jid, room))
      return

    LOG.debug('user %s joined room %s' % (username, room))
    self.check_room_permissions(room, entry, user_obj)

  def set_room_name(self, room, name):
    form = self.plugin['xep_0045'].getRoomForm(room)
    if not form:
      LOG.error("Could not set room name '%s' for room %s" % (name, room))
      return
    values = form.getValues()
    values['muc#roomconfig_roomname'] = name
    form.setValues(values)
    self.plugin['xep_0045'].configureRoom(room, form)

  def _handle_disconnect(self, *args, **kwargs):
    self.scheduler.remove('room_refresh')

  def start(self, event):
    """ Process the session_start event.

    Typical actions for the session_start event are
    requesting the roster and broadcasting an initial
    presence stanza.

    Arguments:
        event -- An empty dictionary. The session_start
                 event does not provide any additional
                 data.
    """
    self.get_roster()
    self.send_presence()
    # run first time
    LOG.debug('Adding init task to scheduler')
    self.schedule('init rooms', 1, self.refresh_rooms, repeat=False)
    # run in intervals
    taskname = 'room_refresh'
    refresh_time = 600
    LOG.debug('Adding task %s to scheduler' % (taskname))
    self.schedule(taskname, refresh_time, self.refresh_rooms, repeat=True)

  def message(self, msg):
    """ Handler for messages sent to us """
    pass
    #print(repr(msg['type']), repr(msg['from']), repr(msg['to']), repr(msg['body']))

  def join_room(self, room, room_name=''):
    LOG.debug('MucBot is now joining room %s' % room)
    self.plugin['xep_0045'].joinMUC(room, self.nick, wait=False)
    LOG.debug('MucBot joined room %s' % room)
    if room_name:
      self.set_room_name(room, room_name)
    self.add_event_handler('muc::%s::got_online' % room, self.user_joined_muc)
    self.rooms[room] = {}

  #def join_room(self, rtype, rid, domain, room_name=''):
  #  room = '%s-%s@%s' % (rtype, str(rid), domain)
  #  LOG.debug('MucBot is now joining room %s' % room)
  #  muc_plug = self.plugin['xep_0045']
  #  muc_plug.joinMUC(room, self.nick, wait=False)
  #  LOG.debug('MucBot joined room %s' % room)
  #  if room_name:
  #    self.set_room_name(room, room_name)
  #  self.add_event_handler('muc::%s::got_online' % room, self.user_joined_muc)
  #  self.rooms[room] = {}

  #def leave_room(self, rtype, rid, domain):
  #  room = '%s-%s@%s' % (rtype, str(rid), domain)
  #  LOG.debug('MucBot is now leaving room %s' % room)
  #  muc_plug = self.plugin['xep_0045']
  #  muc_plug.leaveMUC(room, self.nick)
  #  LOG.debug('MucBot left room %s' % room)
  #  del self.rooms[room]

  def leave_room(self, room):
    LOG.debug('MucBot is now leaving room %s' % room)
    muc_plug = self.plugin['xep_0045']
    muc_plug.leaveMUC(room, self.nick)
    LOG.debug('MucBot left room %s' % room)
    del self.rooms[room]

  def kick_user(self, room, nick):
    try:
      query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
      item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'nick': nick, 'role': 'none'})
      query.append(item)
      iq = self.makeIqSet(query)
      iq['to'] = room
      iq['from'] = None
      try:
        result = iq.send()
        LOG.debug('Result msg after kick_user %s' % repr(result))
      except IqError:
        LOG.exception('Got IqError in kick_users')
        return False
      except IqTimeout:
        LOG.exception('Got IqTimeout in kick_users')
        return False
      return True
    except Exception:
      LOG.exception('Error in kick out')
      return False

  def check_room_permissions(self, room, entry, user_obj):
    nick = unicode(entry['nick'])
    LOG.debug('Checking permissions for nick %s (user id: %s) for room %s' % (nick, user_obj.pk, room))
    if room.startswith('group-'):
      # This is group based chat room
      g_id = int(room.split('@')[0].split('-')[1])
      if not user_obj.user_groups.filter(pk=g_id).exists():
        # User should not be here, kick her out
        self.kick_user(room, nick)
        #self.plugin['xep_0045'].setAffiliation(room, jid=jid, affiliation='outcast')
        LOG.info('kicked nick %s from room %s' % (nick, room))
      else:
        LOG.debug('User %s has right to be in room %s' % (user_obj.pk, room))
    elif room.startswith('role-'):
      # This is role based chat room
      r_id = int(room.split('@')[0].split('-')[1])
      if not user_obj.roles.filter(pk=r_id).exists():
        self.kick_user(room, nick)
        #self.plugin['xep_0045'].setAffiliation(room, jid=jid, affiliation='outcast')
        LOG.info('kicked user %s from room %s' % (nick, room))
      else:
        LOG.debug('User %s has right to be in room %s' % (user_obj.pk, room))
    else:
      LOG.warning("room %s does not start with 'group' or 'role'" % room)

  def refresh_rooms(self):
    LOG.debug('Refreshing rooms')
    db_rooms = []

    def _obj_to_room_name(obj):
      return u'%s / %s' % (obj.organisation.name, obj.name)

    def _obj_to_room_jid(obj, obj_type=None):
      jid = u'%s-%s@%s' % (obj_type, obj.pk, settings.XMPP_MUC_HOST)
      LOG.debug('Translated obj %s to room jid %s' % (repr(obj), jid))
      return jid

    def _join_room(obj, obj_type=None):
      room = _obj_to_room_jid(obj, obj_type)
      room_name = _obj_to_room_name(obj)
      self.join_room(room, room_name)

    for g_id in Group.objects.all().values_list('pk', flat=True):
      jid = u'group-%s@%s' % (g_id, settings.XMPP_MUC_HOST)
      db_rooms.append(jid)

    for r_id in Role.objects.all().values_list('pk', flat=True):
      jid = u'role-%s@%s' % (r_id, settings.XMPP_MUC_HOST)
      db_rooms.append(jid)

    LOG.debug('rooms in db %s ...' % unicode(db_rooms[0:5]))

    existing_rooms = self.rooms.keys()
    LOG.debug('existing rooms %s ...' % existing_rooms[0:5])

    rooms_to_join = set(db_rooms) - set(existing_rooms)
    rooms_to_leave = set(existing_rooms) - set(db_rooms)

    if not rooms_to_join and not rooms_to_leave:
      LOG.debug('No changes in rooms')

    for i in rooms_to_leave:
      LOG.debug('leaving room %s' % i)
      self.leave_room(i)

    for i in rooms_to_join:
      LOG.debug('joining room %s' % i)
      obj_type, obj_id = i.split('@')[0].split('-')
      LOG.debug('obj_type: %s, obj_id: %s for %s' % (obj_type, obj_id, i))
      try:
        if obj_type == 'role':
          obj = Role.objects.get(pk=obj_id)
        elif obj_type == 'group':
          obj = Group.objects.get(pk=obj_id)
      except Exception:
        LOG.exception('Can not join room')
        return
      LOG.debug('joining room for obj %s' % (repr(obj)))
      _join_room(obj, obj_type)


class Command(BaseCommand):
  def handle(self, *args, **options):
    # Setup the MUCBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = MUCBot(settings.XMPP_MUC_USER, settings.XMPP_MUC_PASS, settings.XMPP_MUC_RESOURCE)
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping
    xmpp.register_plugin('old_0004')  # Muc room config form

    # Connect to the XMPP server and start processing XMPP stanzas.
    LOG.debug('Trying to connect to %s:%s' % (settings.XMPP_HOST, settings.XMPP_MUC_PORT))
    if xmpp.connect((settings.XMPP_HOST, settings.XMPP_MUC_PORT)):
      LOG.debug('Connected to %s' % settings.XMPP_HOST)
      xmpp.process(block=True)
    else:
      LOG.error('Mucbot is unable to connect to %s:%s' % (settings.XMPP_HOST, settings.XMPP_MUC_PORT))

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2



import os
import binascii
import logging
import sleekxmpp
from dreammessaging import settings

LOG = logging.getLogger(__name__)


def quick_random_str():
    """Fast random string generator"""
    return binascii.b2a_hex(os.urandom(3))


def get_jid(username):
  jid = '%s@%s' % (username, settings.XMPP_HOST_DOMAIN)
  LOG.debug('jd: %s for username %s' % (jid, username))
  return jid


def get_muc_jid(recpt):
  jid = '%s@%s' % (recpt, settings.XMPP_MUC_HOST)
  LOG.debug('jd: %s for muc recipient %s' % (jid, recpt))
  return jid


def get_password(user):
  api_key = settings.XMPP_AUTH_MASTERKEY
  return 'SERVICE:%s' % api_key


def send_message(user, recipient, message):
  if not settings.XMPP_MUC_HOST:
    LOG.error('XMPP_MUC_HOST is not set in the settings')
  recipient_jid = '%s@%s' % (recipient, settings.XMPP_MUC_HOST)
  host = settings.XMPP_HOST_DOMAIN
  if not host:
    LOG.error('XMPP_HOST_DOMAIN is not set in the settings')
  port = settings.XMPP_PORT
  if not port:
    LOG.error('XMPP_PORT is not set in the settings')
  reattempt = False
  LOG.debug('User %s sending message to recipient %s' % (user.id, recipient_jid), extra={'data': message})
  xmpp = SendXMPPMsg(user, recipient_jid, message)
  LOG.debug('Trying to connect to %s:%s (reattempting: %s)' % (host, port, reattempt))
  if xmpp.connect(address=(host, port), reattempt=False):
    LOG.debug('Connection successful to %s:%s' % (host, port))
    xmpp.process(block=False)
    LOG.debug('message sent from %s to %s' % (user.id, recipient_jid))
  else:
    LOG.error("Connection error. User '%s' could not send message to %s" % (user.id, recipient_jid))


class SendXMPPMsg(sleekxmpp.ClientXMPP):
  def __init__(self, user, room, message):
    LOG.debug('Arrived to SendXMPPMsg init')
    self.user = user
    self.nick = u'%s_%s' % (user.username, quick_random_str())  # This will not be needed with newer ejabberd servers
    LOG.debug(u'Using nick %s' % self.nick)
    self.room = room

    sleekxmpp.ClientXMPP.__init__(self, get_jid(user.username), get_password(user))
    LOG.debug('Init of ClientXMPP done')

    self.use_ipv6 = False
    self.use_message_ids = True
    self.register_plugin('xep_0030')
    self.register_plugin('xep_0045')
    self.register_plugin('xep_0199')

    self.msg = message
    self.add_event_handler('session_start', self.start)
    LOG.debug('Added session_start handler')
    self.add_event_handler("muc::%s::got_online" % self.room, self.muc_online)

  def muc_online(self, presence):
    if presence['muc']['nick'] == self.nick:
      LOG.debug('User %s with nick %s has come online to muc %s' %\
              (self.user.id, self.nick, self.room))
      LOG.debug("User %s ending message with type 'groupchat' to room %s" %\
              (self.user.id, self.room), extra={'data': self.msg})
      self.send_message(mto=self.room, mbody=self.msg, mtype='groupchat')
      LOG.debug('User %s disconnecting from muc room %s' % (self.user.id, self.room))
      self.disconnect(wait=True)

  def start(self, event):
    self.get_roster()
    self.send_presence()
    LOG.debug("User '%s' with nick %s joining to muc room %s in order to send message" %\
            (self.user.id, self.nick, self.room))
    self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


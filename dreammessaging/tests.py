
from django.test import TestCase
from django.conf import settings
from dreammessaging.management.commands import ejabberd_auth_bridge

class EjabberdAuthTestCase(TestCase):

  def test_user_auth(self):
    c = ejabberd_auth_bridge.Command()
    c._handle_auth('testi.oppilas', 'oppil4s')

  def test_service_auth(self):
    c = ejabberd_auth_bridge.Command()
    c._handle_auth('testi.oppilas', 'SERVICE:%s'%settings.XMPP_AUTH_MASTERKEY)

  def test_user_auth_invalid(self):
    c = ejabberd_auth_bridge.Command()
    c._handle_auth('testi.oppilas', 'foo')

  def test_service_auth_invalid(self):
    c = ejabberd_auth_bridge.Command()
    c._handle_auth('testi.oppilas', 'SERVICE:foo')


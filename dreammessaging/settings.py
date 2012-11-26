
from django.conf import settings

XMPP_AUTH_MASTERKEY = getattr(settings, 'XMPP_AUTH_MASTERKEY', '')
XMPP_AUTH_MASTERKEY_ENCODED = getattr(settings, 'XMPP_AUTH_MASTERKEY_ENCODED', '')
XMPP_HOST = getattr(settings, 'XMPP_HOST', '')
XMPP_HOST_DOMAIN = getattr(settings, 'XMPP_HOST_DOMAIN', '')
XMPP_PORT = getattr(settings, 'XMPP_PORT', '')
XMPP_MUC_HOST = getattr(settings, 'XMPP_MUC_HOST', '')



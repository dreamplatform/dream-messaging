
import logging
from django.core.management.base import BaseCommand
from dreamsso.models import User
from dreammessaging.xmpp import send_message

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
      user = User.objects.get(username=args[0])
      send_message(user, args[1], args[2])


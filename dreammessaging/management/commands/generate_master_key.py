
# -*- coding: utf-8 -*-

import string
from random import choice
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

def create_password(size=40):
  return ''.join([choice(string.letters + string.digits) for i in range(size)])

class Command(BaseCommand):
  def handle(self, *args, **options):
    pw = create_password()
    print pw, make_password(pw)

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2


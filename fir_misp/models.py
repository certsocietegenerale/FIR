# -*- coding: utf-8 -*-
from django.db import models

from django.contrib.auth.models import User


class MISPProfile(models.Model):
    api_key = models.TextField(blank=True)
    endpoint = models.TextField(blank=True)
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)

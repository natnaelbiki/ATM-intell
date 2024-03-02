from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        VIEWER = 'VIEWER', _('Viewer')
    
    role = models.CharField(
        max_length=8,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    def __str__(self):
        return self.username

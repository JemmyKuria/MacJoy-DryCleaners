from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('attendant', 'Attendant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendant')

    def __str__(self):
        return f"{self.username} - {self.role}"
    db_table = 'custom_users'
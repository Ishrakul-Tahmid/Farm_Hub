
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
	email = models.EmailField(unique=True)
	is_agent = models.BooleanField(default=False)
	is_farmer = models.BooleanField(default=False)
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

	def __str__(self):
		return self.email

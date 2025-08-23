from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ValidationError


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

User = get_user_model()

class Agent(TimeStampedModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="agent_profile")
    phone = models.CharField(max_length=15, blank=True, null=True)
    locations = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.user.username

class Farm(TimeStampedModel):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_farms")

    def __str__(self) -> str:
        return self.name


class Farmer(TimeStampedModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="farmer_profile")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="farmers")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_farmers")

    def __str__(self) -> str:
        return self.user.username


class Cow(TimeStampedModel):
    tag_id = models.CharField(max_length=64, unique=True)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="cows")
    birth_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_cows")

    def __str__(self) -> str:
        return f"{self.tag_id} ({self.farmer.farm.name})"


class Activity(TimeStampedModel):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_activities")

    class Meta:
        ordering = ["-created_at"]


class MilkRecord(TimeStampedModel):
    cow = models.ForeignKey(Cow, on_delete=models.CASCADE, related_name="milk_records")
    date = models.DateField()
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    recorded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="recorded_milk_records")
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_milk_records")

    class Meta:
        unique_together = ("cow", "date")
        ordering = ["-date", "-created_at"]



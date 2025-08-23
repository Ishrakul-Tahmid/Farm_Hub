from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from farms.models import Activity, Cow, Farm, Farmer, MilkRecord


class Command(BaseCommand):
    help = "Seed the database with example data"

    def handle(self, *args, **options):
        User = get_user_model()

        # Create superuser (admin)
        admin_username = "admin"
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username, email="admin@gmail.com", password="admin@123"
            )
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin'"))

        # Create agent user
        agent, created = User.objects.get_or_create(
            username="agent",
            email="agent@gmail.com",
            defaults={
                "is_staff": True,  # Make agent a staff member
                "first_name": "Agent",
                "last_name": "User"
            }
        )
        agent.set_password("agent@123")
        agent.save()
        self.stdout.write(self.style.SUCCESS("Created agent user 'agent'"))

        # Create farm (by agent)
        farm, _ = Farm.objects.get_or_create(
            name="Green Pastures", 
            defaults={"location": "Valley", "created_by": agent}
        )
        if not farm.created_by:
            farm.created_by = agent
            farm.save()
        self.stdout.write(self.style.SUCCESS("Created farm 'Green Pastures'"))

        # Create farmer user and profile
        farmer_user, created = User.objects.get_or_create(
            username="farmer",
            email="farmer@gmail.com",
            defaults={
                'first_name': 'Farmer',
                'last_name': 'User',
            }
        )
        farmer_user.set_password("farmer@123")
        farmer_user.save()
        
        farmer, _ = Farmer.objects.get_or_create(
            user=farmer_user,
            defaults={"farm": farm, "created_by": agent}
        )
        if not farmer.created_by:
            farmer.created_by = agent
            farmer.save()
        self.stdout.write(self.style.SUCCESS("Created farmer 'farmer'"))

        # Create cows (by farmer)
        cow1, _ = Cow.objects.get_or_create(
            tag_id="COW-001", 
            defaults={"farmer": farmer, "created_by": farmer_user}
        )
        cow2, _ = Cow.objects.get_or_create(
            tag_id="COW-002", 
            defaults={"farmer": farmer, "created_by": farmer_user}
        )
        self.stdout.write(self.style.SUCCESS("Created cows COW-001 and COW-002"))

        # Create milk records (by farmer)
        today = timezone.now().date()
        MilkRecord.objects.get_or_create(
            cow=cow1, 
            date=today, 
            defaults={
                "liters": 12.5, 
                "recorded_by": farmer_user,
                "created_by": farmer_user
            }
        )
        MilkRecord.objects.get_or_create(
            cow=cow2, 
            date=today, 
            defaults={
                "liters": 10.0, 
                "recorded_by": farmer_user,
                "created_by": farmer_user
            }
        )
        self.stdout.write(self.style.SUCCESS("Created milk records"))

        # Create activity (by farmer)
        Activity.objects.get_or_create(
            farmer=farmer, 
            description="Daily milking", 
            actor=farmer_user,
            defaults={"created_by": farmer_user}
        )
        self.stdout.write(self.style.SUCCESS("Created activity"))

        # Create a regular user that can be converted to farmer later
        user1, created = User.objects.get_or_create(
            username="user1",
            email="user1@gmail.com",
            defaults={
                'first_name': 'Regular',
                'last_name': 'User',
            }
        )
        user1.set_password("user1@123")
        user1.save()
        self.stdout.write(self.style.SUCCESS("Created regular user 'user1'"))

        self.stdout.write(self.style.SUCCESS("Seed data created/ensured."))
        self.stdout.write(self.style.SUCCESS("Users: admin/admin, agent/agent, farmer/farmer, user1/user1@123"))



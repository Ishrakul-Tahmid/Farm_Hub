from django.db.models import Avg, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .models import Agent

from .models import Activity, Cow, Farm, Farmer, MilkRecord
from .permissions import (
    ActivityPermission,
    CowPermission,
    FarmPermission,
    FarmerPermission,
    MilkRecordPermission,
    IsAdminUser,
)
from .serializers import (
    ActivitySerializer,
    CowSerializer,
    FarmSerializer,
    FarmerSerializer,
    MilkRecordSerializer,
    AgentSerializer,
)
from . import serializers

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["user__username", "user__first_name", "user__last_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        agent_id = self.kwargs.get("agent_pk")
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        return queryset

    def perform_create(self, serializer):
        agent_id = self.kwargs.get("agent_pk")
        if agent_id:
            serializer.save(agent_id=agent_id, created_by=self.request.user)
        else:
            serializer.save(created_by=self.request.user)


class CowMilkRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MilkRecordSerializer
    permission_classes = [MilkRecordPermission]

    def get_queryset(self):
        return MilkRecord.objects.filter(cow_id=self.kwargs.get('cow_pk')).select_related('recorded_by', 'created_by')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['cow'] = Cow.objects.get(pk=self.kwargs.get('cow_pk'))
        return context

    def perform_create(self, serializer):
        cow = Cow.objects.get(pk=self.kwargs.get('cow_pk'))
        serializer.save(
            cow=cow,
            recorded_by=self.request.user,
            created_by=self.request.user
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, cow_pk=None, **kwargs):  # Add **kwargs parameter here
            qs = self.get_queryset()
            total_liters = qs.aggregate(total=Sum("liters")).get("total") or 0
            total_average = qs.aggregate(average=Avg("liters")).get("average") or 0

            # Get cow and farmer details
            cow_name = "Unknown"
            farmer_name = "Unknown"
            
            try:
                cow = Cow.objects.select_related('farmer', 'farmer__user').get(pk=cow_pk)
                cow_name = cow.tag_id
                farmer_name = cow.farmer.user.username if cow.farmer else "Unknown"
            except Cow.DoesNotExist:
                pass

            return Response({
                "total_liters": float(total_liters),
                "total_average": float(total_average),
                "cow": cow_name,
                "farmer": farmer_name
            })


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    permission_classes = [FarmPermission]
    search_fields = ["name", "location"]
    filterset_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer.objects.select_related("user", "farm").prefetch_related("cows")
    serializer_class = FarmerSerializer
    permission_classes = [FarmerPermission]
    search_fields = ["user__username", "user__first_name", "user__last_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        farm_id = self.kwargs.get("farm_pk")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        return queryset

    def perform_create(self, serializer):
        farm_id = self.kwargs.get("farm_pk")
        if farm_id:
            serializer.save(farm_id=farm_id, created_by=self.request.user)
        else:
            serializer.save(created_by=self.request.user)
    


class CowViewSet(viewsets.ModelViewSet):
    queryset = Cow.objects.select_related("farmer", "farmer__farm")
    serializer_class = CowSerializer
    permission_classes = [CowPermission]
    search_fields = ["tag_id", "farmer__farm__name"]
    filterset_fields = ["farmer__farm"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # If user is a farmer, only show their cows
        if hasattr(user, 'farmer_profile'):
            return queryset.filter(farmer=user.farmer_profile)
        
        # For admin/agents, show all cows or filter by farmer if specified
        farmer_id = self.kwargs.get("farmer_pk")
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        
        return queryset

    def perform_create(self, serializer):
        # The farmer assignment is now handled in the serializer's validate method
        serializer.save(created_by=self.request.user)


class MilkRecordViewSet(viewsets.ModelViewSet):
    queryset = MilkRecord.objects.select_related("cow", "recorded_by", "cow__farmer", "cow__farmer__farm")
    serializer_class = MilkRecordSerializer
    permission_classes = [MilkRecordPermission]
    filterset_fields = ["cow", "cow__farmer", "cow__farmer__farm", "date"]
    search_fields = ["cow__tag_id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        cow_id = self.kwargs.get("cow_pk")
        if cow_id:
            queryset = queryset.filter(cow_id=cow_id)
        return queryset

    def perform_create(self, serializer):
        cow_id = self.kwargs.get("cow_pk")
        if cow_id:
            serializer.save(cow_id=cow_id, recorded_by=self.request.user, created_by=self.request.user)
        else:
            serializer.save(recorded_by=self.request.user, created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, cow_pk=None, **kwargs):  # Add **kwargs here
        qs = self.get_queryset()
        total_liters = qs.aggregate(total=Sum("liters")).get("total") or 0
        total_average = qs.aggregate(average=Avg("liters")).get("average") or 0
        return Response({
            "total_liters": float(total_liters),
            "total_average": float(total_average),
            "cow_id": cow_pk,
            "farmer_id": kwargs.get('farmer_pk')
        })


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("farmer", "actor", "farmer__farm")
    serializer_class = ActivitySerializer
    permission_classes = [ActivityPermission]
    filterset_fields = ["farmer__farm"]
    search_fields = ["description", "actor__username"]

    def get_queryset(self):
        queryset = super().get_queryset()
        farmer_id = self.kwargs.get("farmer_pk")
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        return queryset

    def perform_create(self, serializer):
        farmer_id = self.kwargs.get("farmer_pk")
        if farmer_id:
            serializer.save(farmer_id=farmer_id, actor=self.request.user, created_by=self.request.user)
        else:
            serializer.save(actor=self.request.user, created_by=self.request.user)


# Router setup
router = DefaultRouter()
router.register(r"farms", FarmViewSet, basename="farms") # -->farms
router.register(r"cows", CowViewSet, basename="cows") # -->cows
router.register(r"activities", ActivityViewSet, basename="activities") # -->activities
router.register(r"farmers", FarmerViewSet, basename="farmers") # -->farmers
router.register(r'agents', AgentViewSet, basename="agents") # -->agents


# Nested routers
# Farmers under farms
farms_router = NestedDefaultRouter(router, r"farms", lookup="farm")
farms_router.register(r"farmers", FarmerViewSet, basename="farm-farmers") # -->farm-farmers

# Cows under farms
farmer_cow_router = NestedDefaultRouter(farms_router, r"farmers", lookup="farmer")
farmer_cow_router.register(r"cows", CowViewSet, basename="farmer-cows") # -->farmer-cows

# Milk under cows
farmer_cow_milk = NestedDefaultRouter(farmer_cow_router, r"cows", lookup="cow")
farmer_cow_milk.register(r"milk", CowMilkRecordViewSet, basename="farmer-cow-milk-records") # -->farmer-cow-milk-records

# Milk records under cows
cows_router = NestedDefaultRouter(router, r"cows", lookup="cow")
cows_router.register(r"milk", CowMilkRecordViewSet, basename="cow-milk-records") # -->cow-milk-records

# Activities router
activities_router = NestedDefaultRouter(router, r"farms", lookup="farm")
activities_router.register(r"activities", ActivityViewSet, basename="farm-activities") # -->farm-activities

# farmers --> cows
farmers_cows_router = NestedDefaultRouter(router, r"farmers", lookup="farmer")
farmers_cows_router.register(r"cows", CowViewSet, basename="farmer-cows") # -->farmer-cows

# farmers --> cows --> milk
farmers_cows_milk_router = NestedDefaultRouter(farmers_cows_router, r"cows", lookup="cow")
farmers_cows_milk_router.register(r"milk", CowMilkRecordViewSet, basename="farmer-cow-milk-records") # -->farmer-cow-milk-records



from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Cow


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAgentUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(hasattr(request.user, 'is_agent') and request.user.is_agent and not request.user.is_staff)


class IsFarmerUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(hasattr(request.user, 'is_farmer') and request.user.is_farmer and not request.user.is_staff)


class IsAdminOrAgent(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.is_staff or (hasattr(request.user, 'is_agent') and request.user.is_agent))


class IsAdminOrAgentOrFarmer(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(
            request.user.is_staff or 
            (hasattr(request.user, 'is_agent') and request.user.is_agent) or 
            (hasattr(request.user, 'is_farmer') and request.user.is_farmer)
        )


class MilkRecordPermission(BasePermission):
    def has_permission(self, request, view):
        # Must be authenticated to access milk records
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Get the cow for this milk record
        cow_id = view.kwargs.get('cow_pk')
        try:
            cow = Cow.objects.get(pk=cow_id)
        except Cow.DoesNotExist:
            return False
            
        # Farmers can only access their own cows' records
        if hasattr(request.user, 'farmer_profile'):
            return cow.farmer.user == request.user
            
        # Admin and agents can access all records
        return (request.user.is_staff or request.user.is_agent or request.user.is_farmer)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        # Farmers can only access their own cows' records
        if hasattr(request.user, 'farmer_profile'):
            return obj.cow.farmer.user == request.user
            
        return False


class FarmPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        # Allow create/update/delete only for admin and agents (staff who are not superusers)
        if not request.user or not request.user.is_authenticated:
            return False
            
        return bool(request.user.is_staff or hasattr(request.user, 'is_agent') and request.user.is_agent)

    def has_object_permission(self, request, view, obj):
        # Allow read operations for authenticated users
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        # Only admin and agents can modify farms
        # if request.method in ['PUT', 'PATCH', 'DELETE']:
        return bool(request.user and (request.user.is_staff or request.user.is_agent) )



class FarmerPermission(BasePermission):
    def has_permission(self, request, view):
        # First check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check for admin/staff
        if request.user.is_staff:
            return True

        # Safely check for is_agent
        is_agent = getattr(request.user, 'is_agent', False)
        
        # Allow agents to perform any action
        if is_agent:
            return True

        # For other users (farmers, regular users)
        if request.method in SAFE_METHODS:
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_staff:
            return True

        # Agents can do anything
        if getattr(request.user, 'is_agent', False):
            return True

        # For GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True

        return False



class CowPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only admin, agents, and farmers can create/edit cows
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only admin, the creator, or the farmer can edit
        return bool(
            request.user.is_staff or 
            obj.created_by == request.user or 
            obj.farmer.user == request.user
        )


class MilkRecordPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only admin, agents, and farmers can create/edit milk records
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only admin, the creator, or the farmer can edit
        return bool(
            request.user.is_staff or 
            obj.created_by == request.user or 
            obj.cow.farmer.user == request.user
        )


class ActivityPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # Only admin, agents, and farmers can create/edit activities
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
            
        # Admin can edit any activity
        if request.user.is_staff:
            return True
            
        # Agents can edit activities they created or in their farms
        if request.user.is_agent:
            return True
            
        # Farmers can only edit activities related to them
        if request.user.is_farmer:
            return obj.farmer.user == request.user

        if obj.created_by == request.user:
            return True

        return False



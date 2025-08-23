from django.contrib.auth import get_user_model
from django.forms import ValidationError
from rest_framework import serializers


from .models import Activity, Agent, Cow, Farm, Farmer, MilkRecord, User
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name", "email"]

class AgentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = Agent
        fields = ['id', 'user', 'user_id', 'phone', 'locations', 
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_user_id(self, value):
        if value.is_staff:
            raise serializers.ValidationError(
                "Admin users cannot be registered as agents."
            )
        if value.is_farmer:
            raise serializers.ValidationError(
                "Farmers cannot be registered as agents."
            )
        if Agent.objects.filter(user=value).exists():
            raise serializers.ValidationError(
                "This user is already registered as an agent."
            )
        return value

    def create(self, validated_data):
        user = validated_data.get('user')
        if user and not user.is_agent:
            user.is_agent = True
            user.save(update_fields=['is_agent'])
        
        # Remove any created_by field if it exists
        validated_data.pop('created_by', None)
        
        agent = Agent.objects.create(**validated_data)
        return agent

    def update(self, instance, validated_data):
        user = validated_data.get('user')
        if user and user != instance.user:
            # Update is_agent flags if user is changed
            instance.user.is_agent = False
            instance.user.save(update_fields=['is_agent'])
            
            user.is_agent = True
            user.save(update_fields=['is_agent'])
        
        # Remove any created_by field if it exists
        validated_data.pop('created_by', None)
        
        return super().update(instance, validated_data)


class MilkRecordSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MilkRecord
        fields = ['id', 'date', 'liters', 'recorded_by', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['recorded_by', 'created_by']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
            
        # Ensure the user has access to this cow's records
        cow = self.context.get('cow')
        if not cow:
            raise serializers.ValidationError("Cow not found")
            
        if hasattr(request.user, 'farmer_profile'):
            # If user is a farmer, they can only add records for their own cows
            if cow.farmer.user != request.user:
                raise serializers.ValidationError("You can only add milk records for your own cows")
                
        return attrs
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name", "email"]


class FarmSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    farmers_count = serializers.SerializerMethodField()
    

    class Meta:
        model = Farm
        fields = ["id", "name", "location", "created_by", "farmers_count", "created_at", "updated_at"]
        read_only_fields = ["created_by", "farmers_count"]

    def get_farmers_count(self, obj):
        return obj.farmers.count()



class FarmerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    farm = FarmSerializer(read_only=True)
    farm_id = serializers.PrimaryKeyRelatedField(
        queryset=Farm.objects.all(),
        source='farm',
        write_only=True,
        required=False
    )
    cows_count = serializers.SerializerMethodField()

    class Meta:
        model = Farmer
        fields = ['id', 'user', 'user_id', 'farm', 'farm_id', 'created_by', 'cows_count', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'cows_count', 'created_at', 'updated_at']

    def get_cows_count(self, obj):
        return obj.cows.count()

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_staff and not getattr(user, 'is_agent', False):
            raise serializers.ValidationError("Only admin and agents can create farmers.")
        return attrs
    
    def validate_user_id(self, value):
        # Check if user is already a farmer
        if Farmer.objects.filter(user=value).exists():
            raise serializers.ValidationError(
                f"User {value.email} is already registered as a farmer."
            )
        
        # Check if user is an agent - using is_agent property
        if hasattr(value, 'is_agent') and value.is_agent:
            raise serializers.ValidationError(
                f"User {value.email} is an agent and cannot be registered as a farmer."
            )
        
        # Check if user is admin/staff
        if value.is_staff:
            raise serializers.ValidationError(
                "Admin users cannot be registered as farmers."
            )
            
        return value

    def create(self, validated_data):
        is_farmer = validated_data.pop('is_farmer', True)
        user = validated_data.get('user')
        
        # Set is_farmer flag on user
        if user and not user.is_farmer:
            user.is_farmer = is_farmer
            user.save(update_fields=['is_farmer'])
        
        # Create the farmer instance
        farmer = Farmer.objects.create(**validated_data)
        return farmer

    def update(self, instance, validated_data):
        is_farmer = validated_data.pop('is_farmer', None)
        
        # Update is_farmer flag if provided
        if is_farmer is not None and instance.user.is_farmer != is_farmer:
            instance.user.is_farmer = is_farmer
            instance.user.save(update_fields=['is_farmer'])
        
        return super().update(instance, validated_data)

class CowSerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer(read_only=True)
    farmer_id = serializers.PrimaryKeyRelatedField(
        queryset=Farmer.objects.all(), source="farmer", write_only=True,
        required=False  # Make it optional since we'll set it automatically for farmers
    )
    created_by = UserSerializer(read_only=True)
    milk_records_count = serializers.SerializerMethodField()

    class Meta:
        model = Cow
        fields = ["id", "tag_id", "farmer", "farmer_id", "birth_date", "created_by", "milk_records_count", "created_at", "updated_at"]
        read_only_fields = ["created_by", "milk_records_count"]

    def get_milk_records_count(self, obj):
        return obj.milk_records.count()

    def validate(self, attrs):
        user = self.context['request'].user
        
        # Check if user is a farmer
        if hasattr(user, 'farmer_profile'):
            # For farmers, we'll use their own farmer profile
            attrs['farmer'] = user.farmer_profile
        elif not user.is_staff:
            raise serializers.ValidationError({
                "permission": "Only admin, agents, and farmers can create cows."
            })
        elif 'farmer' not in attrs:
            # Admin/agents must provide a farmer_id
            raise serializers.ValidationError({
                "farmer_id": "Farmer ID is required for admin and agents"
            })

        return attrs


class MilkRecordSerializer(serializers.ModelSerializer):
    cow = CowSerializer(read_only=True)
    cow_id = serializers.PrimaryKeyRelatedField(
        queryset=Cow.objects.all(), source="cow", write_only=True
    )
    recorded_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MilkRecord
        fields = [
            "id",
            "cow",
            "cow_id",
            "date",
            "liters",
            "recorded_by",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["recorded_by", "created_by"]

    def validate(self, attrs):
        # Only admin, agents, and farmers can create milk records
        user = self.context['request'].user
        if not user.is_staff and not hasattr(user, 'farmer_profile'):
            raise serializers.ValidationError("Only admin, agents, and farmers can create milk records.")
        return attrs


class ActivitySerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer(read_only=True)
    farmer_id = serializers.PrimaryKeyRelatedField(
        queryset=Farmer.objects.all(), source="farmer", write_only=True
    )
    actor = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ["id", "farmer", "farmer_id", "actor", "description", "created_by", "created_at", "updated_at"]
        read_only_fields = ["created_by"]

    def validate(self, attrs):
        # Only admin, agents, and farmers can create activities
        user = self.context['request'].user
        if not user.is_staff and not hasattr(user, 'farmer_profile'):
            raise serializers.ValidationError("Only admin, agents, and farmers can create activities.")
        return attrs



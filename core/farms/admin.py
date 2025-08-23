from django.contrib import admin

from .models import Activity, Cow, Farm, Farmer, MilkRecord, Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_is_agent', 'phone', 'locations', 'created_at']
    list_filter = ['user__is_agent', 'created_at']
    search_fields = ['user__email', 'user__username', 'phone', 'locations']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_username(self, obj):
        return obj.user.email
    get_username.short_description = 'User'
    get_username.admin_order_field = 'user__email'

    def get_is_agent(self, obj):
        return obj.user.is_agent
    get_is_agent.short_description = 'Is Agent'
    get_is_agent.boolean = True
    get_is_agent.admin_order_field = 'user__is_agent'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Agent Details', {
            'fields': ('phone', 'locations')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new agents
            obj.user.is_agent = True
            obj.user.save()
        super().save_model(request, obj, form, change)

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_by")
    search_fields = ("name", "location")
    list_filter = ("created_by",)


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_farmer", "farm", "created_by")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("farm", "created_by")
    
    def is_farmer(self, obj):
        return obj.user.is_farmer
    is_farmer.boolean = True
    is_farmer.short_description = "Is Farmer"

@admin.register(Cow)
class CowAdmin(admin.ModelAdmin):
    list_display = ("tag_id", "farmer", "birth_date", "created_by")
    list_filter = ("farmer__farm", "created_by")
    search_fields = ("tag_id",)


@admin.register(MilkRecord)
class MilkRecordAdmin(admin.ModelAdmin):
    list_display = ("cow", "date", "liters", "recorded_by", "created_by")
    list_filter = ("date", "cow__farmer__farm")
    search_fields = ("cow__tag_id",)
    autocomplete_fields = ("cow", "recorded_by")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("farmer", "description", "actor", "created_at", "created_by")
    list_filter = ("farmer__farm", "created_by")
    search_fields = ("description", "actor__username")



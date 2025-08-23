from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Browsable API login/logout links (top right)
    path("api/auth/django/", include("rest_framework.urls")),
    # Djoser auth URLs
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("users.urls")),  # custom additions like logout blacklist
    # JWT endpoints (Djoser provides optional JWT routes too, we expose DRF-SJWT directly)
    path("api/auth/jwt/create/", TokenObtainPairView.as_view(), name="jwt-create"),
    path("api/auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("api/auth/jwt/verify/", TokenVerifyView.as_view(), name="jwt-verify"),
    path("api/", include("farms.urls")),
    path("users/", include("users.urls")),
]



from django.urls import include, path

from .views import (
    activities_router,
    cows_router,
    farms_router,
    router,
    farmer_cow_router,
    farmer_cow_milk,
    farmers_cows_router,
    farmers_cows_milk_router,
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(farms_router.urls)),
    path("", include(cows_router.urls)),
    path("", include(activities_router.urls)),
    path("", include(farmer_cow_router.urls)),
    path("", include(farmer_cow_milk.urls)),
    path("", include(farmers_cows_router.urls)),
    path("", include(farmers_cows_milk_router.urls)),
]



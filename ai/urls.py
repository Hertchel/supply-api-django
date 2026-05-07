from django.urls import path

from .views import (
    AIRecommendationView,
    AIForecastView,
    AIAnomalyView
)

urlpatterns = [

    path(
        'recommendations/',
        AIRecommendationView.as_view()
    ),

    path(
        'forecast/',
        AIForecastView.as_view()
    ),

    path(
        'anomalies/',
        AIAnomalyView.as_view()
    ),
]
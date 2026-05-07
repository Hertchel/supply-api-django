
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.anomaly_service import (
    detect_anomalies

)

from .services.forecast_service import (
    forecast_item_demand
)

from .services.recommendation_service import (
    generate_purchase_recommendations
)


class AIRecommendationView(APIView):

    def get(self, request):

        recommendations = (
            generate_purchase_recommendations()
        )

        return Response(recommendations)


class AIForecastView(APIView):

    def get(self, request):

        forecast = forecast_item_demand()

        return Response(forecast)
    

class AIAnomalyView(APIView):

    def get(self, request):

        anomalies = detect_anomalies()

        return Response(anomalies)
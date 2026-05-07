
from rest_framework.views import APIView
from rest_framework.response import Response

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

    def get(self, request, item_id):

        return Response({
            "item_id": item_id,
            "predicted_demand": 35
        })


class AIAnomalyView(APIView):

    def get(self, request):

        anomalies = [
            {
                "item": "Laptop",
                "requested_quantity": 100,
                "reason": "Unusually high request"
            }
        ]

        return Response(anomalies)
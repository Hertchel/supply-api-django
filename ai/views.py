from rest_framework.views import APIView
from rest_framework.response import Response


class AIRecommendationView(APIView):

    def get(self, request):

        data = [
            {
                "item": "Bond Paper",
                "current_stock": 10,
                "recommended_order": 50
            },
            {
                "item": "Printer Ink",
                "current_stock": 5,
                "recommended_order": 20
            }
        ]

        return Response(data)


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
from collections import defaultdict
from decimal import Decimal

from api.models import Item


def generate_purchase_recommendations():

    item_usage = defaultdict(float)

    items = Item.objects.all()

    for item in items:

        try:

            quantity = float(item.quantity)

        except Exception:

            quantity = 0

        item_usage[
            item.item_description
        ] += quantity

    recommendations = []

    for item_name, total_quantity in item_usage.items():

        if total_quantity >= 5:

            recommended_order = (
                total_quantity + 10
            )

            recommendations.append({

                "item": item_name,

                "monthly_usage":
                    round(total_quantity, 2),

                "recommended_order":
                    round(recommended_order, 2),

                "reason":
                    "High procurement demand"
            })

    recommendations.sort(
        key=lambda x: x["monthly_usage"],
        reverse=True
    )

    return recommendations
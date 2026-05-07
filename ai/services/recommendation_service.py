from collections import defaultdict

from api.models import Item


def generate_purchase_recommendations():

    item_usage = defaultdict(int)

    items = Item.objects.all()

    for item in items:

        item_usage[
            item.item_description
        ] += int(item.quantity)

    recommendations = []

    for item_name, total_quantity in item_usage.items():

        if total_quantity >= 5:

            recommended_order = (
                total_quantity + 10
            )

            recommendations.append({

                "item": item_name,

                "monthly_usage":
                    total_quantity,

                "recommended_order":
                    recommended_order,

                "reason":
                    "High procurement demand"
            })

    recommendations.sort(
        key=lambda x: x["monthly_usage"],
        reverse=True
    )

    return recommendationse
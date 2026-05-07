from api.models import StockItems
from api.models import Item


def generate_purchase_recommendations():

    recommendations = []

    stock_items = StockItems.objects.all()

    for stock in stock_items:

        item_name = (
            stock.supplier_item
            .item_quotation
            .item
            .item_description
        )

        current_stock = stock.quantity_on_hand

        usage_count = Item.objects.filter(
            item_description=item_name
        ).count()

        reorder_point = usage_count * 2

        if current_stock <= reorder_point:

            suggested_order = (
                reorder_point
                - current_stock
                + 10
            )

            recommendations.append({

                "item": item_name,

                "current_stock": current_stock,

                "monthly_usage": usage_count,

                "recommended_order":
                    suggested_order
            })

    return recommendations
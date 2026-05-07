import pandas as pd
from inventory.models import InventoryItem
from procurement.models import PurchaseRequest

def generate_purchase_recommendations():

    inventory = InventoryItem.objects.all()

    recommendations = []

    for item in inventory:

        monthly_usage = PurchaseRequest.objects.filter(
            item=item
        ).count()

        reorder_point = monthly_usage * 2

        if item.quantity <= reorder_point:

            suggested_quantity = reorder_point - item.quantity + 10

            recommendations.append({
                "item": item.item_name,
                "current_stock": item.quantity,
                "monthly_usage": monthly_usage,
                "recommended_order": suggested_quantity
            })

    return recommendations
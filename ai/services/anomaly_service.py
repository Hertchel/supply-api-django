from statistics import mean

from api.models import Item


def detect_anomalies():

    items = Item.objects.all()

    quantities = []

    for item in items:

        try:

            quantities.append(
                float(item.quantity)
            )

        except Exception:

            pass

    if not quantities:

        return []

    average_quantity = mean(quantities)

    threshold = average_quantity * 3

    anomalies = []

    for item in items:

        try:

            quantity = float(item.quantity)

        except Exception:

            quantity = 0

        if quantity >= threshold:

            anomalies.append({

                "item":
                    item.item_description,

                "requested_quantity":
                    quantity,

                "average_quantity":
                    round(average_quantity, 2),

                "reason":
                    "Unusually high procurement quantity",

                "purchase_request":
                    item.purchase_request.pr_no
            })

    return anomalies
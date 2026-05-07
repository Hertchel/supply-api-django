from procurement.models import PurchaseRequest

def detect_anomalies():

    requests = PurchaseRequest.objects.all()

    anomalies = []

    average_quantity = 0

    total = 0

    for req in requests:
        total += req.quantity

    if requests.count() > 0:
        average_quantity = total / requests.count()

    threshold = average_quantity * 3

    for req in requests:

        if req.quantity > threshold:

            anomalies.append({
                "pr_number": req.pr_no,
                "item": req.item.item_name,
                "requested_quantity": req.quantity,
                "average_quantity": average_quantity,
                "reason": "Unusually high request"
            })

    return anomalies
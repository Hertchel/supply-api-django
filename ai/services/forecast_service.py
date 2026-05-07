import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

from procurement.models import PurchaseRequest

def forecast_item_demand(item_id):

    requests = PurchaseRequest.objects.filter(
        item_id=item_id
    ).order_by('created_at')

    if requests.count() < 2:
        return {
            "forecast": "Not enough data"
        }

    data = []

    for index, req in enumerate(requests):
        data.append([
            index,
            req.quantity
        ])

    df = pd.DataFrame(data, columns=['month', 'quantity'])

    X = df[['month']]
    y = df['quantity']

    model = LinearRegression()
    model.fit(X, y)

    future_month = [[len(df) + 1]]

    prediction = model.predict(future_month)

    return {
        "predicted_demand": round(prediction[0], 2)
    }
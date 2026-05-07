import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression

from api.models import Item


def forecast_item_demand():

    items = Item.objects.all().order_by(
        "created_at"
    )

    if items.count() < 2:

        return {
            "message":
                "Not enough historical data"
        }

    data = []

    for index, item in enumerate(items):

        try:

            quantity = float(item.quantity)

        except Exception:

            quantity = 0

        data.append({

            "month": index + 1,

            "quantity": quantity,

            "item":
                item.item_description
        })

    df = pd.DataFrame(data)

    X = df[["month"]]

    y = df["quantity"]

    model = LinearRegression()

    model.fit(X, y)

    future_month = np.array([
        [len(df) + 1]
    ])

    prediction = model.predict(
        future_month
    )

    return {

        "historical_records":
            len(df),

        "predicted_next_month_demand":
            round(
                float(prediction[0]),
                2
            ),

        "trend":
            "Increasing procurement demand"
            if prediction[0] > y.mean()
            else "Stable procurement demand"
    }   
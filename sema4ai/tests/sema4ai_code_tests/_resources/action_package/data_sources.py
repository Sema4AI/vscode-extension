from typing import Annotated

from sema4ai.data import DataSource, DataSourceSpec

FileChurnDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="churn",
        file="files/customer-churn.csv",
        engine="files",
        description="Ddts.",
    ),
]

ChurnPredictionDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="models",
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which provides along with a table named `customer_churn_predictor`.",
        setup_sql="""
            CREATE MODEL IF NOT EXISTS models.customer_churn_predictor
            FROM files
            (SELECT * FROM churn)
            PREDICT Churn;
    """,
    ),
]

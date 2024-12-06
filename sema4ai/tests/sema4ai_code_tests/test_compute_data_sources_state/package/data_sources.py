from typing import Annotated

from sema4ai.data import DataSource, DataSourceSpec

# Generated data source (files:can be configured automatically)
CustomersDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="customers_in_test_compute_data_sources_state",
        file="files/customers.csv",
        engine="files",
        description="Data source for customers.",
    ),
]

# Generated data source (models:can be configured automatically)
PredictDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        model_name="predict_compute_data_sources_state",
        engine="prediction:lightwood",
        description="Predict something.",
        sql="""
CREATE MODEL models.predict_compute_data_sources_state
(SELECT * FROM files.customers)
PREDICT country
ORDER BY first_name
WINDOW 8
HORIZON 4;""",
    ),
]

# External data source (needs to be configured separately)
TestSqliteDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="test_compute_data_sources_state",
        engine="sqlite",
        description="Data source for tests.",
    ),
]

from typing import Annotated

from sema4ai.data import DataSource, DataSourceSpec

# Generated data source (can be configured automatically)
CustomersDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="customers_in_test_compute_data_sources_state",
        file="files/customers.csv",
        engine="files",
        description="Data source for customers.",
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

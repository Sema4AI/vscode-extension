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

# External data source (needs to be configured separately)
TestSqliteDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="test_compute_data_sources_state",
        engine="sqlite",
        description="Data source for tests.",
    ),
]


# CustomerSupportTicketsDataSource = Annotated[
#     DataSource,
#     DataSourceSpec(
#         created_table="customer_support_tickets",
#         file="files/customer_support_tickets.csv",
#         engine="files",
#         description="Data source for historical Customer support tickets data.",
#     ),
# ]

WikipediaKnowledgeBaseDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="wikipedia_kb",
        engine="sema4_knowledge_base",
        description="Data source for the knowledge base of Wikipedia articles.",
    ),
]

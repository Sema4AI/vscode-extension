from sema4ai.data import query

from .data_sources import CustomersDataSource


@query
def get_customers_data(customers_data_source: CustomersDataSource) -> str:
    """
    Query the customers data
    Arguments:
        customers_data_source: The datasource to access files/customers.csv file
    Returns:
        The customers information as a markdown table.
    """
    result = customers_data_source.query("SELECT * FROM customers LIMIT 10;")
    return result.to_markdown()

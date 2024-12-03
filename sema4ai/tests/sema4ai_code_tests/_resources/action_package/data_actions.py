from typing import Annotated

from data_sources import ChurnPredictionDataSource, FileChurnDataSource
from sema4ai.data import DataSource, predict, query


@query
def get_churn_data(datasource: FileChurnDataSource) -> str:
    """
    Query the customer churn
    Arguments:
        datasource: The datasource to access files/churn.csv file
    Returns:
        The churn information as a markdown table.
    """
    result = datasource.query("SELECT * FROM churn LIMIT 10;")
    return result.to_markdown()


@predict
def predict_churn(
    datasource: Annotated[DataSource, ChurnPredictionDataSource | FileChurnDataSource],
    limit: int = 10,
) -> str:
    """
    This predict will predict churn for a given number of customers.

    Arguments:

        datasource: The datasource to use for the prediction.
        limit: The maximum number of customers to predict for.

    Returns:
        Details of the prediction.
    """
    sql = """
    SELECT t.customerID AS customer_id, t.Contract AS contract, t.MonthlyCharges AS monthly_charges, m.Churn AS churn
    FROM files.churn AS t
    JOIN models.customer_churn_predictor AS m
    LIMIT $limit;
    """

    result = datasource.query(sql, params={"limit": limit})
    return result.to_markdown()

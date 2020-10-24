# azureml-core of version 1.0.72 or higher is required
# azureml-dataprep[pandas] of version 1.1.34 or higher is required
from azureml.core import Workspace, Dataset

subscription_id = 'b6dd5ca5-4289-4490-b104-d8426cd804c4'
resource_group = 'aviation.ai'
workspace_name = 'aviationai-ml'

workspace = Workspace(subscription_id, resource_group, workspace_name)

dataset = Dataset.get_by_name(workspace, name='flightdata_clean')
dataset.to_pandas_dataframe()
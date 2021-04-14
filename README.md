## SmallGCPProject

GCP Project to move data from GCP Bucket storage to BigQuery.

### Installation

This project needs the following components installed on your GCP Platform. Open your GCP Console and run the followings:

#### Create temporal folder

__Clone from Github__

- Open your GCP Cloud console shell and clone the repo `git clone https://github.com/KenrySanchez/SmallGCPProject`.

#### Creating streaming source and destination sinks

To stream content into BigQuery, you need to have a `FILES_SOURCE Cloud Storage bucket` and a destination `table in BigQuery`.

__Create your Bucket__

- Source = ${DEVSHELL_PROJECT_ID}-<your_bucket_name>.
- gsutil mb -c regional -l <your_prefer_region> gs://${FILES_SOURCE}.

NOTE: I use the `us-central1` region for example. You must have your components in the same region to reduce cost and latency.

__Create your BigQuery Table__

- bq mk <dataset_name>.
- bq mk <dataset_name>.<table_name> schema.json.
- bq ls --format=pretty mydataset

The Output must be like:

+---------+-------+--------+-------------------+
| tableId | Type  | Labels | Time Partitioning |
+---------+-------+--------+-------------------+
| mytable | TABLE |        |                   |
+---------+-------+--------+-------------------+

#### Deploy GCP function

We need to create another Bucket for storage the function. Then, we can deploy the function to connect the whole pipeline. Run the following on console:

- FUNCTIONS_BUCKET=${DEVSHELL_PROJECT_ID}-functions.
- gsutil mb -c regional -l <your_region> gs://${FUNCTIONS_BUCKET}.
- At the `SmallGCPProject` root folder run

```
gcloud functions deploy streaming --region=<your_region> \
    --source=./SmallGCPProject --runtime=python37 \
    --stage-bucket=${FUNCTIONS_BUCKET} \
    --trigger-bucket=${FILES_SOURCE}
```

This will deploy the function for trigger when upload files in the bucked assigned for the json objects. Once the deployment is finished, go to `CLOUD FUNCTION` and at the admin panel, you must see the function deployed successfully.

#### Prepare GCP Dataflow template

To prepare dataflow for run when trigger functions, we must do the followings:

__Install Apache Beam SDK__

- We must initalize GCP Dataflow, follow the guidelines for the first time initializing (Usually, it's at the right side of the panel. This will show up if you never have used dataflow before).
- Then, on your console run `pip install apache-beam[gcp]`.

__Prepare dataflow template__

We need to prepare a new Bucket Storage which will be used as a repository for the dataflow job (it saves temp and stagging files).

- Go to `GCP Bucket` and create a new bucket (you can also run `gsutil mb -c regional -l <your_prefer_region> gs://dataflow_assets`).
- Inside of it, create three new folders `temp, stagging and template`.
- Go to the `template` folder inside of your `SmallGCPProject` folder, using your gcp console.
- Then, run:

```
python DataFlowRun.py --runner DataFlowRunner --project <gcp_project_id> --staging_location gs://dataflow_assets/stagging/ --temp_location gs://dataflow_assets/temp/ --template_location gs://dataflow_assets/templates/myTemplate --setup_file /home/<your_username>/SmallGCPProject/template/setup.py  --save_main_session True --region us-central1
```

This will generate a dataflow template at the `gs://dataflow_assets/templates/`.

NOTE: if you don't use the `dataflow_assets` name, remember to change it in the snippet above. 

### Usage

Everytime you upload a new object which match with the `schema.json`, this will run a apache beam job to process the data and insert new rows at your BigQuery table.

The idea using dataflow is that if you need to build a better pipeline or generate new fields for insert in your table, you can do it easily using python and apache beam. GCP Dataflow offers a smart way for follow the data extraction and insertion inside any gcp component.

### Contribution

If you need to change the way of insertion in your BigQuery table, feel free to change the `schema.json` file. Also, you will need to prepare the new feature inside the dict object at `line 44` in DataFlowRun.py. Also, you'd need to change the `BigQuery schema` (you will do this in the BigQuery Admin Panel), as well as change the dataflow schema at `line 64` in DataFlowRun.py.
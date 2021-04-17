# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


'''
This Cloud function is responsible for:
- Parsing and validating new files added to Cloud Storage.
- Checking for duplications.
- Inserting files' content into BigQuery.
- Logging the ingestion status into Cloud Firestore and Stackdriver.
- Publishing a message to either an error or success topic in Cloud Pub/Sub.
'''

import json
import logging
import os
import traceback
from datetime import datetime

from google.api_core import retry
from google.cloud import bigquery
from google.cloud import storage
from googleapiclient.discovery import build
import pytz

PROJECT_ID = os.getenv("logo-project-306822")
BQ_DATASET = "logo_dataset"
BQ_TABLE = "logo_table"
CS = storage.Client()
BQ = bigquery.Client()


def streaming(data, context):

    bucket_name = data["bucket"]
    file_name = data["name"]
    try:
        _insert_into_bigquery(bucket_name, file_name, str(data["timeCreated"]))
    except Exception as e:
        logging.error(e)


def _insert_into_bigquery(bucket_name, file_name, time_exec):

    project = "logo-project-306822"
    job = project + " " + time_exec

    #path of the dataflow template on google storage bucket
    template = "gs://logo_dataflow_assets/templates/myTemplate"
    inputFile = "gs://" + bucket_name + "/" + file_name

    parameters = {
        "input": inputFile
    }

    environment = {"tempLocation": "gs://logo_dataflow_assets/temp"}
    service = build("dataflow", "v1b3", cache_discovery=False)

    request = service.projects().locations().templates().launch(
        projectId=project,
        gcsPath=template,
        location="us-central1",
        body={
            "jobName": job,
            "parameters": parameters,
            "environment": environment
        },
    )

    response = request.execute()
    print(str(response))

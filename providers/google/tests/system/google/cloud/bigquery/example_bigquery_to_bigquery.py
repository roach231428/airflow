#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
Airflow System Test DAG that verifies BigQueryToBigQueryOperator.
"""

from __future__ import annotations

import os
from datetime import datetime

from airflow.models.dag import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryCreateTableOperator,
    BigQueryDeleteDatasetOperator,
)
from airflow.providers.google.cloud.transfers.bigquery_to_bigquery import BigQueryToBigQueryOperator
from airflow.utils.trigger_rule import TriggerRule

ENV_ID = os.environ.get("SYSTEM_TESTS_ENV_ID", "default")
DAG_ID = "bigquery_to_bigquery"

DATASET_NAME = f"dataset_{DAG_ID}_{ENV_ID}"
ORIGIN = "origin"
TARGET = "target"
LOCATION = "US"
SCHEMA = [
    {"name": "emp_name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "salary", "type": "INTEGER", "mode": "NULLABLE"},
]


with DAG(
    DAG_ID,
    schedule="@once",
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example", "bigquery"],
) as dag:
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset",
        dataset_id=DATASET_NAME,
        location=LOCATION,
    )

    create_origin_table = BigQueryCreateTableOperator(
        task_id="create_origin_table",
        dataset_id=DATASET_NAME,
        table_id="origin",
        table_resource={
            "schema": {"fields": SCHEMA},
        },
    )

    create_target_table = BigQueryCreateTableOperator(
        task_id="create_target_table",
        dataset_id=DATASET_NAME,
        table_id="target",
        table_resource={
            "schema": {"fields": SCHEMA},
        },
    )

    # [START howto_operator_bigquery_to_bigquery]
    copy_selected_data = BigQueryToBigQueryOperator(
        task_id="copy_selected_data",
        source_project_dataset_tables=f"{DATASET_NAME}.{ORIGIN}",
        destination_project_dataset_table=f"{DATASET_NAME}.{TARGET}",
    )
    # [END howto_operator_bigquery_to_bigquery]

    delete_dataset = BigQueryDeleteDatasetOperator(
        task_id="delete_dataset",
        dataset_id=DATASET_NAME,
        delete_contents=True,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    (
        # TEST SETUP
        create_dataset
        >> [create_origin_table, create_target_table]
        # TEST BODY
        >> copy_selected_data
        # TEST TEARDOWN
        >> delete_dataset
    )

    from tests_common.test_utils.watcher import watcher

    # This test needs watcher in order to properly mark success/failure
    # when "tearDown" task with trigger rule is part of the DAG
    list(dag.tasks) >> watcher()


from tests_common.test_utils.system_tests import get_test_run  # noqa: E402

# Needed to run the example DAG with pytest (see: tests/system/README.md#run_via_pytest)
test_run = get_test_run(dag)

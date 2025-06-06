 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.



Callbacks
=========

A valuable component of logging and monitoring is the use of task callbacks to act upon changes in state of a given task, or across all tasks in a given DAG.
For example, you may wish to alert when certain tasks have failed, or have the last task in your DAG invoke a callback when it succeeds.

.. note::

    Callback functions are only invoked when the task state changes due to execution by a worker.
    As such, task changes set by the command line interface (:doc:`CLI <../../howto/usage-cli>`) or user interface (:doc:`UI <../../ui>`) do not
    execute callback functions.

.. warning::

    Callback functions are executed after tasks are completed.
    Errors in callback functions will show up in scheduler logs rather than task logs.
    By default, scheduler logs do not show up in the UI and instead can be found in
    ``$AIRFLOW_HOME/logs/scheduler/latest/DAG_FILE.py.log``

Callback Types
--------------

There are five types of task events that can trigger a callback:

=========================================== ================================================================
Name                                        Description
=========================================== ================================================================
``on_success_callback``                     Invoked when the task :ref:`succeeds <concepts:task-instances>`
``on_failure_callback``                     Invoked when the task :ref:`fails <concepts:task-instances>`
``on_retry_callback``                       Invoked when the task is :ref:`up for retry <concepts:task-instances>`
``on_execute_callback``                     Invoked right before the task begins executing.
``on_skipped_callback``                     Invoked when the task is :ref:`running <concepts:task-instances>` and  AirflowSkipException raised.
                                            Explicitly it is NOT called if a task is not started to be executed because of a preceding branching
                                            decision in the DAG or a trigger rule which causes execution to skip so that the task execution
                                            is never scheduled.
=========================================== ================================================================


Example
-------

In the following example, failures in any task call the ``task_failure_alert`` function, and success in the last task calls the ``dag_success_alert`` function:

.. code-block:: python

    import datetime
    import pendulum

    from airflow.sdk import DAG
    from airflow.providers.standard.operators.empty import EmptyOperator


    def task_failure_alert(context):
        print(f"Task has failed, task_instance_key_str: {context['task_instance_key_str']}")


    def dag_success_alert(context):
        print(f"DAG has succeeded, run_id: {context['run_id']}")


    with DAG(
        dag_id="example_callback",
        schedule=None,
        start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
        dagrun_timeout=datetime.timedelta(minutes=60),
        catchup=False,
        on_success_callback=dag_success_alert,
        on_failure_callback=None,
        tags=["example"],
    ):
        task1 = EmptyOperator(task_id="task1")
        task2 = EmptyOperator(task_id="task2")
        task3 = EmptyOperator(task_id="task3", on_failure_callback=[task_failure_alert])
        task1 >> task2 >> task3

.. note::
    As of Airflow 2.6.0, callbacks now supports a list of callback functions, allowing users to specify multiple functions
    to be executed in the desired event. Simply pass a list of callback functions to the callback args when defining your DAG/task
    callbacks: e.g ``on_failure_callback=[callback_func_1, callback_func_2]``

Full list of variables available in ``context`` in :doc:`docs <../../templates-ref>` and `code <https://github.com/apache/airflow/blob/main/task-sdk/src/airflow/sdk/definitions/context.py>`_.

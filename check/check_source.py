#!/usr/bin/env python3
import requests
import json


def check_source_connector(connect_url: str = "http://localhost:8084"):
    """Check detailed status of the Postgres source connector"""

    connector_name = "postgres-connector"

    print("\n=== Connector Configuration ===")
    config_response = requests.get(f"{connect_url}/connectors/{connector_name}/config")
    if config_response.status_code == 200:
        config = config_response.json()
        print(json.dumps(config, indent=2))
    else:
        print(f"Failed to get config: {config_response.status_code}")

    print("\n=== Connector Status ===")
    status_response = requests.get(f"{connect_url}/connectors/{connector_name}/status")
    if status_response.status_code == 200:
        status = status_response.json()
        print(json.dumps(status, indent=2))
    else:
        print(f"Failed to get status: {status_response.status_code}")

    print("\n=== Task Status ===")
    tasks_response = requests.get(f"{connect_url}/connectors/{connector_name}/tasks")
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()
        for task in tasks:
            task_id = task["id"]
            task_status_response = requests.get(
                f"{connect_url}/connectors/{connector_name}/tasks/{task_id['task']}/status"
            )
            if task_status_response.status_code == 200:
                task_status = task_status_response.json()
                print(f"\nTask {task_id['task']}:")
                print(json.dumps(task_status, indent=2))
    else:
        print(f"Failed to get tasks: {tasks_response.status_code}")


if __name__ == "__main__":
    check_source_connector()

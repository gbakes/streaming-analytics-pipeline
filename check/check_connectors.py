#!/usr/bin/env python3
import requests
import json
from typing import Dict, Any
import sys


def print_separator():
    print("\n" + "=" * 80 + "\n")


def test_connect_access(connect_url: str) -> bool:
    """Test basic connectivity to Kafka Connect"""
    try:
        print(f"Testing connection to {connect_url}")
        response = requests.get(connect_url)
        print(f"Connect response status code: {response.status_code}")
        if response.status_code == 200:
            print("Successfully connected to Kafka Connect")
            return True
        else:
            print(f"Failed to connect. Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Failed to connect to {connect_url}")
        print(f"Error details: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error connecting to Kafka Connect: {str(e)}")
        return False


def get_connector_list(connect_url: str) -> list:
    """Get list of all connectors"""
    try:
        response = requests.get(f"{connect_url}/connectors")
        if response.status_code == 200:
            connectors = response.json()
            print(f"\nFound {len(connectors)} connectors: {', '.join(connectors)}")
            return connectors
        else:
            print(f"Failed to get connector list. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting connector list: {str(e)}")
        return []


def check_single_connector(connect_url: str, connector: str) -> None:
    """Check status and configuration of a single connector"""
    print_separator()
    print(f"Checking connector: {connector}")

    try:
        config_response = requests.get(f"{connect_url}/connectors/{connector}/config")
        print("\nConfiguration Response Status:", config_response.status_code)
        if config_response.status_code == 200:
            config = config_response.json()
            print("\nConfiguration:")
            print(json.dumps(config, indent=2))
        else:
            print(f"Failed to get config: {config_response.text}")
    except Exception as e:
        print(f"Error getting connector config: {str(e)}")

    try:
        status_response = requests.get(f"{connect_url}/connectors/{connector}/status")
        print("\nStatus Response Status:", status_response.status_code)
        if status_response.status_code == 200:
            status = status_response.json()
            print("\nStatus:")
            print(f"Connector State: {status['connector']['state']}")

            if "tasks" in status:
                for task in status["tasks"]:
                    print(f"\nTask {task['id']}:")
                    print(f"State: {task['state']}")
                    if task["state"] == "FAILED":
                        print("Error Trace:")
                        print(task.get("trace", "No error trace available"))
        else:
            print(f"Failed to get status: {status_response.text}")
    except Exception as e:
        print(f"Error getting connector status: {str(e)}")


def main():
    connect_url = "http://localhost:8084"

    print("Starting Kafka Connect Debug")
    print_separator()

    if not test_connect_access(connect_url):
        print("Cannot proceed with checks due to connection failure")
        sys.exit(1)

    connectors = get_connector_list(connect_url)

    if not connectors:
        print("No connectors found or couldn't retrieve connector list")
        return

    for connector in connectors:
        check_single_connector(connect_url, connector)

    print_separator()
    print("Debug check completed")


if __name__ == "__main__":
    main()

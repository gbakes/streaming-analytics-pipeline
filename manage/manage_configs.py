#!/usr/bin/env python3
import argparse
import json
import os

import requests
import urllib3.exceptions
import yaml
from dotenv import load_dotenv
from minio import Minio
from urllib3 import PoolManager, Timeout
from urllib3.exceptions import MaxRetryError


class ConfigManager:
    def __init__(
        self,
        config_path="configs/connectors.yaml",
        minio_config_path="configs/minio.yaml",
    ):
        load_dotenv()

        connect_port = os.getenv("CONNECT_PORT", "8084")
        self.connect_url = f"http://localhost:{connect_port}"

        self.config_path = config_path
        self.minio_config_path = minio_config_path
        self.load_configs()

    def load_configs(self):
        """Load and process configurations with environment variables"""
        with open(self.config_path, "r") as f:
            self.connector_configs = yaml.safe_load(f)
        with open(self.minio_config_path, "r") as f:
            self.minio_config = yaml.safe_load(f)

        self.process_env_vars(self.connector_configs)
        self.process_env_vars(self.minio_config)

    def process_env_vars(self, config):
        """Recursively process environment variables in configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                if (
                    isinstance(value, str)
                    and value.startswith("${")
                    and value.endswith("}")
                ):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self.process_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                if isinstance(item, (dict, list)):
                    self.process_env_vars(item)

    def setup_minio(self):
        """Setup MinIO buckets and policies"""
        try:
            minio_endpoint = "localhost:9000"
            print(f"Connecting to MinIO at: {minio_endpoint}")

            self.minio_client = Minio(
                minio_endpoint,
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                secure=False,
            )

            self.bucket_name = "retail-data"
            try:
                if not self.minio_client.bucket_exists(self.bucket_name):
                    self.minio_client.make_bucket(self.bucket_name)
                    print(f"Created bucket: {self.bucket_name}")
                else:
                    print(f"Bucket already exists: {self.bucket_name}")
            except Exception as e:
                print(f"Error creating bucket {self.bucket_name}: {str(e)}")

        except MaxRetryError as e:
            print(
                f"Failed to connect to MinIO. Make sure the service is running. Error: {str(e)}"
            )
        except Exception as e:
            print(f"Error setting up MinIO: {str(e)}")
            raise

    def get_existing_connectors(self):
        """Get list of existing connectors"""
        try:
            response = requests.get(f"{self.connect_url}/connectors")
            return response.json()
        except requests.exceptions.ConnectionError:
            print(
                "Failed to connect to Kafka Connect. Make sure the service is running."
            )
            return []

    def delete_connector(self, name):
        """Delete a connector"""
        try:
            response = requests.delete(f"{self.connect_url}/connectors/{name}")
            if response.status_code in [204, 404]:
                print(f"Deleted connector: {name}")
            else:
                print(f"Failed to delete connector {name}: {response.text}")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Kafka Connect")

    def create_or_update_connector(self, name, config):
        """Create or update a connector"""
        try:
            response = requests.get(f"{self.connect_url}/connectors/{name}")

            if response.status_code == 200:
                response = requests.put(
                    f"{self.connect_url}/connectors/{name}/config",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(config["config"]),
                )
                print(f"Updated connector: {name}")
            else:
                response = requests.post(
                    f"{self.connect_url}/connectors",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(config),
                )
                print(f"Created connector: {name}")

            if response.status_code not in [200, 201]:
                print(f"Failed to configure connector {name}: {response.text}")

        except requests.exceptions.ConnectionError:
            print("Failed to connect to Kafka Connect")
        except Exception as e:
            print(f"Error configuring connector {name}: {str(e)}")

    def apply_configs(self):
        """Apply all configurations"""
        print("Setting up MinIO...")
        self.setup_minio()

        print("\nConfiguring connectors...")
        for connector_name, config in self.connector_configs["connectors"].items():
            self.create_or_update_connector(config["name"], config)

    def delete_all_connectors(self):
        """Delete all existing connectors"""
        existing_connectors = self.get_existing_connectors()
        for connector in existing_connectors:
            self.delete_connector(connector)


def main():
    parser = argparse.ArgumentParser(description="Manage Kafka Connect configurations")
    parser.add_argument(
        "--action",
        choices=["apply", "delete"],
        default="apply",
        help="Action to perform (apply or delete configurations)",
    )
    args = parser.parse_args()

    manager = ConfigManager()

    if args.action == "apply":
        manager.apply_configs()
    elif args.action == "delete":
        manager.delete_all_connectors()


if __name__ == "__main__":
    main()

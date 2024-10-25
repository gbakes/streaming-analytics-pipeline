#!/usr/bin/env python3
import yaml
import requests
import json
import argparse
from minio import Minio
from urllib3.exceptions import MaxRetryError
import os
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_path='configs/connectors.yaml', minio_config_path='configs/minio.yaml'):
        # Load environment variables
        load_dotenv()
        
        self.connect_url = os.getenv('CONNECT_URL', 'http://localhost:8084')
        self.config_path = config_path
        self.minio_config_path = minio_config_path
        self.load_configs()

    def load_configs(self):
        """Load and process configurations with environment variables"""
        with open(self.config_path, 'r') as f:
            self.connector_configs = yaml.safe_load(f)
        with open(self.minio_config_path, 'r') as f:
            self.minio_config = yaml.safe_load(f)
        
        # Process environment variables in configs
        self.process_env_vars(self.connector_configs)
        self.process_env_vars(self.minio_config)

    def process_env_vars(self, config):
        """Recursively process environment variables in configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
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
            minio_client = Minio(
                self.minio_config['minio']['endpoint'].replace('http://', ''),
                access_key=self.minio_config['minio']['access_key'],
                secret_key=self.minio_config['minio']['secret_key'],
                secure=False
            )

            for bucket in self.minio_config['minio']['buckets']:
                try:
                    if not minio_client.bucket_exists(bucket['name']):
                        minio_client.make_bucket(bucket['name'])
                        print(f"Created bucket: {bucket['name']}")
                    else:
                        print(f"Bucket already exists: {bucket['name']}")
                except Exception as e:
                    print(f"Error creating bucket {bucket['name']}: {str(e)}")

        except MaxRetryError:
            print("Failed to connect to MinIO. Make sure the service is running.")
        except Exception as e:
            print(f"Error setting up MinIO: {str(e)}")

    def get_existing_connectors(self):
        """Get list of existing connectors"""
        try:
            response = requests.get(f'{self.connect_url}/connectors')
            return response.json()
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Kafka Connect. Make sure the service is running.")
            return []

    def delete_connector(self, name):
        """Delete a connector"""
        try:
            response = requests.delete(f'{self.connect_url}/connectors/{name}')
            if response.status_code in [204, 404]:
                print(f"Deleted connector: {name}")
            else:
                print(f"Failed to delete connector {name}: {response.text}")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Kafka Connect")

    def create_or_update_connector(self, name, config):
        """Create or update a connector"""
        try:
            # Check if connector exists
            response = requests.get(f'{self.connect_url}/connectors/{name}')
            
            if response.status_code == 200:
                # Update existing connector
                response = requests.put(
                    f'{self.connect_url}/connectors/{name}/config',
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(config['config'])
                )
                print(f"Updated connector: {name}")
            else:
                # Create new connector
                response = requests.post(
                    f'{self.connect_url}/connectors',
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(config)
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
        for connector_name, config in self.connector_configs['connectors'].items():
            self.create_or_update_connector(config['name'], config)

    def delete_all_connectors(self):
        """Delete all existing connectors"""
        existing_connectors = self.get_existing_connectors()
        for connector in existing_connectors:
            self.delete_connector(connector)

def main():
    parser = argparse.ArgumentParser(description='Manage Kafka Connect configurations')
    parser.add_argument('--action', choices=['apply', 'delete'], default='apply',
                      help='Action to perform (apply or delete configurations)')
    args = parser.parse_args()

    manager = ConfigManager()
    
    if args.action == 'apply':
        manager.apply_configs()
    elif args.action == 'delete':
        manager.delete_all_connectors()

if __name__ == "__main__":
    main()
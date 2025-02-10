# CDC to MinIO Project

This project sets up a Change Data Capture (CDC) pipeline from PostgreSQL to MinIO using Debezium and Kafka Connect.

## Architecture

```
PostgreSQL -> Debezium -> Kafka -> S3 Sink Connector -> MinIO
```

## Components

- PostgreSQL: Source database
- Debezium: Change Data Capture
- Apache Kafka: Message streaming
- Kafka Connect: Connector framework
- MinIO: S3-compatible object storage

## Directory Structure

- `configs/`: Contains connector and MinIO configurations
- `scripts/`: Python scripts for managing connectors
- `docs/`: Additional documentation
- `.env.example`: Example environment variables
- `docker-compose.yml`: Docker services configuration
- `Dockerfile.connect`: Custom Kafka Connect image with connectors

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cdc-minio-project
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

3. Start the services:
```bash
docker-compose up -d
```

4. Install Python dependencies:
```bash
pip install pyyaml requests minio python-dotenv
```

5. Apply connector configurations:
```bash
python scripts/manage_configs.py --action apply
```

## Data Organization

The data in MinIO is organized by domain:

```
s3://my-bucket/
├── customers/
│   ├── raw/
│   └── addresses/
├── orders/
│   ├── raw/
│   └── items/
└── products/
    └── raw/
```

## Configuration

- Connector configurations are in `configs/connectors.yaml`
- MinIO settings are in `configs/minio.yaml`
- Environment variables are defined in `.env`

## Usage

1. Start/Stop Services:
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down
```

2. Manage Connectors:
```bash
# Apply configurations
python scripts/manage_configs.py --action apply

# Delete configurations
python scripts/manage_configs.py --action delete
```

## Maintenance

- Monitor connector status:
```bash
curl -X GET http://localhost:8084/connectors/<connector-name>/status | jq
```

- View logs:
```bash
docker-compose logs -f connect
```

## MINIO 

`mc alias set myminio http://localhost:9000 minio minio123`
`mc mb myminio/bucket1`

Go to: http://localhost:9001 

Username: minio
Password: minio123

## Debezium sink

`curl http://localhost:8084/connectors` to give the connector names

To see the state of the connector:
`curl -X GET http://localhost:8084/connectors/postgres-connector/status | jq`

`curl -X GET http://localhost:8084/connectors/status | jq`


### db changes

To make db changes you can execute:

``` bash
podman compose exec postgres psql -U postgres -d mydb -c "
INSERT INTO customers (name, email) VALUES 
    ('George Baker', 'gb@example.com');"
```

### Kafka chanes
To view all the changes in the topic:
```
podman compose exec kafka kafka-console-consumer \
    --bootstrap-server kafka:9092 \
    --topic postgres-server.public.customers \
    --from-beginning
```

## Managing configs:

`python3 manage_configs.py --action apply`


## Minio config for event listening

mc config host list 
mc admin info retail-minio
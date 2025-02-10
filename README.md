# Overview

This is a project template for local testing of glue pipelines.

## Setup

### .env file

Setup requires a .env file in the project directory with the following variables:

* REPO_DIR
* POSTGRES_HOST
* POSTGRES_DB
* POSTGRES_USER
* POSTGRES_PASSWORD

The POSTGRES_ prefixed variable can be named anything except for POSTGRES_HOST which needs to take the container name of the postgres service 'localdb'. The REPO_DIR variable needs to be the location of the project directory. You can start setting those up using:

```{bash}
touch .env
echo "\nREPO_DIR=$(pwd)" >> .env
echo "\POSTGRES_HOST=localdb" >> .env
```

### AWS Credentials + Glue

The AWS Glue development environment is configured to run locally with AWS credentials. The service mounts your local AWS credentials directory (`~/.aws`) into the container at `/home/glue_user/.aws`. This allows the container to use your existing AWS profiles and credentials.

The environment is configured using the `AWS_PROFILE` variable from the local environment and sets the default region to `eu-west-1`. Access to the local workspace is provided through volume mounting `${REPO_DIR}` to `/home/glue_user/workspace/jupyter_workspace`, enabling direct access to your project files within the containerized environment. 
The service exposes ports 8888 for Jupyter notebook access.

You'll need to copy the aws credentials (option 2) into the `~/.aws/credentials` file and make sure that the profile name matches the one set in the `AWS_PROFILE` variable.

### Postgres
Environment variables for the database configuration are managed through a `.env` file described above. Connection to this database via PGAdmin4 can be done using the same credentials but using `localhost` as the hostname.

The init.sql file is run on database creation to manage the working tables.


## Running

With the above set up you can now run:

`podman compose -f docker-compose.yml -p data-local-testing up -d --build` 

To create the containers. From there jupyter notebooks are accessible via `localhost:8888` and the `local_data_pipeline` container is accessible via devcontainers in vscode.

In a devcontainer terminal run:

```
python3 trading_datamart/sample.py 
python3 trading_datamart/trading_datamart.py --GLUE_GAMEPLAY_DB data-dev-gameplay-pipeline-glue-catalog-db --GLUE_PLAY_TABLE gameplay_pipeline_glue_play_table_v2
```
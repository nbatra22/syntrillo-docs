# healthie_dev

Healthie API development environment

## Modules

### Healthie

Package with functions connecting with Healthie's API and GraphQL

## Organization folders

Each folder include a dot env file `.env` with api keys generated in Healthie > Settings

These files are local files, not stored in the repository.

```
API_KEY='xxxx'
ORGANIZATION='staging'  # 'staging' or 'production'
```

### Staging folder

staging account, organization id 57057

### Production folder

production/enterprise account, organization id 8387


## Requirements & Environments

Locally, using anaconda development environment, named 'syntrillo'

`requirement.txt` created & updated manually

`environement.yml` created with `conda env export --name syntrillo --file environment.yml`

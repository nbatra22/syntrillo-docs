# Healthie App Development Repository

`healthie_dev` repository hosted by Syntrillo : https://github.com/Syntrillo/healthie_dev

Objectives:
  - provides an interface to Healthie's API and endpoints
  - provides an interface to Syntrillo's iFrames displayed in Healthie extra tabs and panel items
  - provides HTML content to be delivered into Healthie iFrames (currently the SyntrilloPythonAnywhere web-server app)
  - includes the logic to all Healthie's related events
  - will have to interact with other repositories: eg care plans, tenovi, virtucal care navigator, ...

## Architecture

```
.
|-- modules                 : python modules
|   |-- data                : management of data structures
|   |   `-- structures      : clinician-friendly Excel files with list of variables
|   |                         organized by Intake Forms or Charting Notes
|   `-- healthie            : communication and analysis logic
|       `-- llm             : initial test with LLM
|-- prod                    : code for Healthie production
`-- staging                 : code for Healthie staging
```

Note : the data structures are placed in this repository since they are specific to Healthie's Intake Flow and UI.


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

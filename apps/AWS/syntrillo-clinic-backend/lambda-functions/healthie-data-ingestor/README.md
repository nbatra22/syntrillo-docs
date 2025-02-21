# Healthie Data Ingestor service

### Table of contents
- [What data do we need to ingest?](#what-data-do-we-need-to-ingest)
  - [Forms definitions](#forms-definitions)
  - [Form responses](#form-responses)

- [Questions for Omar](#question-for-omar)
- [Questions and answers to help Alex](#questions-and-answers-to-help-alex)
- [TODOs for Pau](#todos-for-pau)

### What data do we need to ingest?

We need to track
- Forms definitions -> `healthie.forms` (slowly changing dimensions table)
- Form responses -> `healthie.form_responses` (fact table)

We daily sync the data from Healthie to our Amzon RDS.
From there, the Amazon Data Migration Service will copy the data to a raw data bucket on S3 (aka data lake).

Once we have the data in S3, we need to transform it into a more usable format for our analytics and reporting. But this is something we do in the data warehouse, not here.

### Forms definitions

We can get a full snapshot of all the forms in our Healthie DB with this query. This query needs to run
every day, as clinicians can update forms over time (not so often), and create new ones.

```graphql
query formTemplates(
  $include_default_templates: Boolean
  $active_status: Boolean
  $should_paginate: Boolean
  $category: String
  $keywords: String
  $offset: Int
  $sortBy: String
) {
  customModuleForms(
    include_default_templates: $include_default_templates
    active_status: $active_status
    should_paginate: $should_paginate
    category: $category
    keywords: $keywords
    offset: $offset
    sort_by: $sortBy
  ) {
    id
    name
    prefill
    uploaded_by_healthie_team
    custom_modules {
      id
      mod_type
      options
      label
    }
  }
}
```

The response will be a nested JSON, that we can transform into a flat dictionary with the following keys, that we can push to the `healthie.forms` table in Amazon RDS.

`healthie.forms` table would have columns:

- `form_id`: unique identifier for the form (primary key)
- `form_name`: human readable name of the form
- `module_id`: unique identifier for this module in the form (primary key)
- `module_label`: question text
- `module_options`: answer options
  - `null`: for questions that don't have options, e.g. text input

There is a field called `module_type` which is a string, not an enum. It looks very inconsistent, probably
because each clinician can define their own question types. By manually inspectin the data, I saw
the following types:
  - `"label"`: this is not a question, it's just a text label
  - `"radio"`: multiple choice
  - `"horizontal_radio"`: multiple choice
  - `"checkbox"`: multiple choice
  - `"textarea"`: text input
  - `"date"`: date input
  - ...

My recommendation is to not use the `module_type` field at all.

### Form responses

We need to track the responses to the forms that patients (or sometimes clinicians) fill out.

```graphql
query formAnswerGroups(
  $date: String, # e.g "2021-10-29" using type ISO8601DateTime does not work
  $custom_module_form_id: ID, # e.g "11"
  ) {
  formAnswerGroups(
    date: $date,
    custom_module_form_id: $custom_module_form_id,
    ) {
    name
    custom_module_form {
      id
    }
    created_at
    form_answers {
      label
      displayed_answer
      created_at
      user_id
      custom_module {
        id
      }
    }
  }
}
```

The response will be a nested JSON, that we can transform into a flat dictionary with the following keys, that we can push to the `healthie.form_responses` table in Amazon RDS.

`healthie.form_responses` table would have columns:

- `form_id`: unique identifier for the form (primary key)
- `module_id`: unique identifier for this module in the form (primary key)
- `user_id`: unique identifier for the patient or clinician who filled out the form (primary key)
- `answer`: answer to the question, from the `"displayed_answer"` field in the response
- `created_at`: date and time when the answer was submitted

## Question for Omar

- What about capturing forms that are sent to patients but not answered?
  - Is this a potential sign of risk we should collect in our DB?

## Questions and answers to help Alex
- How to run a GraphQL query to fetch data from Healthie
  [Check this](https://github.com/Syntrillo/SyntrilloClinic/blob/e207f714a5ccdde39569b9e29026aaff0525dc6d/sources/syntrillo/api_healthie/forms.py#L44)

- How to create the two tables we need `healthie.forms` and `healthie.form_responses`
  [This is the file with some example queries](https://github.com/Syntrillo/SyntrilloClinic/blob/prod/apps/AWS/syntrillo-clinic-backend/utils/database/create-or-recreate-tables.sql)

## TODOs for Pau

- Quick docs on how to:
  - Run an SQL query against our AWS RDS.
  - How to define a new table in our database.



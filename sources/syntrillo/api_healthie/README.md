# Healthie API connection and management scripts

Package with functions connecting with Healthie's API and GraphQL


Objectives:
  - provides an interface to Healthie's API and endpoints
  - provides an interface to Syntrillo's iFrames displayed in Healthie extra tabs and panel items
  - provides HTML content to be delivered into Healthie iFrames (currently the SyntrilloPythonAnywhere web-server app)
  - includes the logic to all Healthie's related events

## Environment files

Include api keys generated in Healthie > Settings

These files are local files, not stored in the repository.

```
API_KEY='xxxx'
ORGANIZATION='staging'  # 'staging' or 'production'
```

### Accounts :

staging account, organization id 57057

production/enterprise account, organization id 8387


## CustomModuleForm graph

```mermaid
graph TD;
    CustomModuleForm["<b>CustomModuleForm</b><br/>A template for a form, that can then be filled out<br/><a href='https://docs.gethealthie.com/schema/custommoduleform.doc'>Docs</a>"];
    CustomModule["<b>CustomModule</b><br/>A question in a template<br/><a href='https://docs.gethealthie.com/schema/custommodule.doc'>Docs</a>"];
    custom_modules["<b>custom_modules</b><br/>The questions in the template"];
    form_answer_groups["<b>form_answer_groups</b><br/>All filled out forms for this template"];
    FormAnswerGroup["<b>FormAnswerGroup</b><br/>A completed form, with metadata about the completion, and the saved answers<br/><a href='https://docs.gethealthie.com/schema/formanswergroup.doc'>Docs</a>"];
    form_answers["<b>form_answers</b><br/>The visible answers for the filled form"];
    FormAnswer["<b>FormAnswer</b><br/>An answer in a filled form<br/><a href='https://docs.gethealthie.com/schema/formanswer.doc'>Docs</a>"];

    CustomModuleForm --> custom_modules;
    custom_modules --> CustomModule;
    CustomModuleForm --> form_answer_groups;
    form_answer_groups --> FormAnswerGroup;
    FormAnswerGroup --> form_answers;
    form_answers --> FormAnswer;

```

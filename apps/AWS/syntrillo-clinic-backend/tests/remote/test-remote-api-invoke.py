import _invoke_remote_api

resource_path = "/static/healthie.css"
api_name = "IFramGeneratorAPI"
invoke_method = "GET"
headers = {"Content-Type": "application/json"}
body = "{}"

_invoke_remote_api.invoke_api_resource(resource_path, api_name, invoke_method, headers, body)
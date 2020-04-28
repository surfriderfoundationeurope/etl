import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    path = req.params.get('path')
    file_type = req.params.get('file_type')
    if not path:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            path = req_body.get('path')
            file_type = req_body.get('file_type')

    if path and file_type:
        return func.HttpResponse(f"We're going to process {path} with {file_type} method! ")

    else:
        return func.HttpResponse(
             "Please pass a path and a file_type on the query string or in the request body",
             status_code=400
        )

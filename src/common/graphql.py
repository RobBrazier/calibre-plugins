from urllib import request, error
import json
import logging

logger = logging.getLogger(__name__)


class GraphQLClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.token = None

    def set_token(self, token: str):
        self.token = token

    def execute(self, query: str, variables: dict | None = None, timeout=30):
        data = {"query": query, "variables": variables}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if self.token:
            token = self.token
            if (
                " " not in self.token
            ):  # does it have a 'prefix' like Bearer already there?
                token = f"Bearer {token}"
            headers["Authorization"] = token

        body = json.dumps(data).encode("utf-8")

        req = request.Request(self.endpoint, body, headers)

        try:
            res = request.urlopen(req, timeout=timeout)
            body = res.read()
            json_result = json.loads(body.decode("utf-8"))
            if "data" in json_result:
                json_result = json_result.get("data")
            return json_result
        except error.HTTPError as e:
            logger.exception("GraphQL request failed")
            raise e

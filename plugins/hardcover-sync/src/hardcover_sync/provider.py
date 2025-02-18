from graphql.client import GraphQLClient


class HardcoverProvider:
    API_URL = "https://api.hardcover.app/v1/graphql"

    def __init__(self, source):
        self.source = source
        self.client = GraphQLClient(self.API_URL)


from urllib.parse import urljoin


class Settings:
    schema = 'https'
    host = 'lgqm.gq'
    api_path = '/api/mobile/'
    limit_length = 300
    @property
    def server(self):
        return f'{self.schema}://{self.host}/'

    @property
    def api(self):
        return urljoin(self.server, self.api_path)

default_settings = Settings()

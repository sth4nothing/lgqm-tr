import os
from urllib.parse import urljoin


class Settings:
    schema = 'https'
    host = 'lgqm.gq'
    api_path = '/api/mobile/'
    data_dir = './data/'
    limit_length = 0
    @property
    def server(self):
        return f'{self.schema}://{self.host}/'

    @property
    def api(self):
        return urljoin(self.server, self.api_path)

    @property
    def cookies_path(self):
        return os.path.join(self.data_dir, 'cookies.json')

default_settings = Settings()

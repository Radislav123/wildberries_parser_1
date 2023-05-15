from selenium.webdriver import Chrome


class BasePage:
    # элементы url
    scheme: str
    domain: str
    path: str
    parameters = {}

    def __init__(self, driver: Chrome) -> None:
        self.driver = driver

    def open(self) -> None:
        self.driver.get(self.url)

    @property
    def url(self) -> str:
        return self.construct_url()

    def construct_url(self, scheme = None, domain = None, path = None, parameters = None) -> str:
        if scheme is None:
            scheme = self.scheme
        if domain is None:
            domain = self.domain
        if path is None:
            path = self.path
        if parameters is None:
            parameters = self.parameters

        url = f"{scheme}://{domain}/{path}"
        if parameters:
            url += '?'
            for parameter_name in parameters:
                url += f"{parameter_name}={parameters[parameter_name]}&"
            url = url[:-1]
        return url

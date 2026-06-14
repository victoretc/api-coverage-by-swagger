import json
import uuid
from json.decoder import JSONDecodeError
from typing import Any

import httpx
import structlog
from curlify2 import Curlify

from httpx import URL


class Configuration:
    def __init__(
        self, *, base_url: URL | str = "", disable_log: bool = False, **kwargs: Any
    ) -> None:
        """
        Parameters:
            base_url (optional):
                A URL to use as the base when building request URLs.

            disable_log (bool, optional):
                Disables logging if set to True. Defaults to False.

            auth (optional):
                An authentication class to use when sending requests.

            params (optional):
                Query parameters to include in request URLs, as a string, dictionary,
                or sequence of two-tuples.

            headers (optional):
                Dictionary of HTTP headers to include when sending requests.

            cookies (optional):
                Dictionary of Cookie items to include when sending requests.

            verify (optional):
                Either `True` to use an SSL context with the default CA bundle,
                `False` to disable verification, or an instance of `ssl.SSLContext`
                to use a custom context.

            http2 (optional):
                A boolean indicating if HTTP/2 support should be enabled. Defaults to `False`.

            proxy (optional):
                A proxy URL where all the traffic should be routed.

            timeout (optional):
                The timeout configuration to use when sending requests.

            limits (optional):
                The limits configuration to use.

            max_redirects (optional):
                The maximum number of redirect responses that should be followed.

            transport (optional):
                A transport class to use for sending requests over the network.

            trust_env (optional):
                Enables or disables usage of environment variables for configuration.

            default_encoding (optional):
                The default encoding to use for decoding response text, if no charset
                information is included in a response Content-Type header. Set to a
                callable for automatic character set detection. Default: "utf-8".

        """
        self.base_url = base_url
        self.disable_log = disable_log
        self.kwargs = kwargs


class Logging:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.log = structlog.get_logger(__name__).bind(service="api")

    def log_request(self, method: str, url: str, **kwargs: Any) -> None:
        log = self.log.bind(event_id=str(uuid.uuid4()))
        json_data = kwargs.get("json")
        content = kwargs.get("content")
        try:
            if content:
                json_data = json.loads(content)
        except JSONDecodeError:
            ...

        msg = dict(
            event="Request",
            method=method,
            path=url,
            host=self.configuration.base_url,
            params=kwargs.get("params"),
            headers=kwargs.get("headers"),
            data=kwargs.get("data"),
        )

        if isinstance(json_data, dict):
            msg["json"] = json_data

        log.msg(**msg)

    def log_response(self, response: httpx.Response) -> None:
        log = self.log.bind(event_id=str(uuid.uuid4()))
        curl = Curlify(response.request).to_curl()
        print(curl)
        log.msg(
            event="Response",
            status_code=response.status_code,
            headers=dict(response.headers),
            content=self._get_json(response),
        )

    @staticmethod
    def _get_json(response: httpx.Response) -> dict[str, Any] | bytes:
        try:
            return response.json()
        except JSONDecodeError:
            return response.content


class Client(httpx.Client):
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        super().__init__(
            base_url=self.configuration.base_url, **self.configuration.kwargs
        )
        self._logger = Logging(self.configuration)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        if not self.configuration.disable_log:
            self._logger.log_request(method, url, **kwargs)

        response = super().request(method, url, **kwargs)

        if not self.configuration.disable_log:
            self._logger.log_response(response)

        return response


__all__ = ["Configuration", "Client"]

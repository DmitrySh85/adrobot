import logging
from json import JSONDecodeError
from typing import Any

import requests
from adrobot.settings import KEITARO_API_HOST, KEITARO_API_TOKEN
from .types import (
    Offer,
    Domain,
    Source,
    Group,
    CampaignPayload,
    FlowPayload,
    FlowAction,
    Campaign,
    Flow,
    APIResponse
)



class KeitaroAPIManager:

    def __init__(
        self,
        api_host=KEITARO_API_HOST,
        api_token = KEITARO_API_TOKEN
    ):
        self.api_host = api_host
        self.api_token = api_token

    def get_offers(self) -> list[Offer]:
        url = f"{self.api_host}offers"
        data = self._send_get_request(url)
        return data

    def get_domains(self) -> list[Domain]:
        url = f"{self.api_host}domains"
        data = self._send_get_request(url)
        return data

    def get_sources(self) -> list[Source]:
        url = f"{self.api_host}traffic_sources"
        data = self._send_get_request(url)
        return data

    def get_groups(self) -> list[Group]:
        # NOTE: External API endpoint https://tlgk.host/admin_api/v1/groups may respond with 400 in some environments.
        url = f"{self.api_host}groups"
        data = self._send_get_request(url)
        return data

    def get_flow_actions(self) -> list[FlowAction]:
        url = f"{self.api_host}streams_actions"
        return self._send_get_request(url)

    def get_campaigns(self) -> list[Campaign]:
        url = f"{self.api_host}campaigns"
        return self._send_get_request(url)

    def get_campaign(self, campaign_id: int) -> Campaign:
        url = f"{self.api_host}campaigns/{campaign_id}"
        return self._send_get_request(url)

    def get_flows(self, campaign_id: int) -> list[Flow]:
        url = f"{self.api_host}campaigns/{campaign_id}/streams"
        return self._send_get_request(url)

    def create_campaign(self, payload: CampaignPayload) -> dict[str, Any] | None:
        url = f"{self.api_host}campaigns"
        return self._send_post_request(url, payload)

    def create_flow(self, payload: FlowPayload) -> dict[str, Any] | None:
        url = f"{self.api_host}streams"
        return self._send_post_request(url, payload)

    def update_flow(self, flow_id: int, payload: FlowPayload) -> list[Flow]:
        url = f"{self.api_host}streams/{flow_id}"
        return self._send_put_request(url, payload)

    def _send_put_request(
            self,
            url: str,
            payload: dict[str, Any]
    ) -> APIResponse | None:
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        try:
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except JSONDecodeError:
            logging.warning(f"Failed to decode JSON from {url}")
        except requests.exceptions.RequestException as exc:
            logging.warning(f"PUT request to {url} failed: {exc}")
        return None

    def _send_post_request(
            self,
            url: str,
            payload: dict[str, Any]
    ) -> APIResponse | None:
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except JSONDecodeError:
            logging.warning(f"Failed to decode JSON from {url}")
        except requests.exceptions.RequestException as exc:
            logging.warning(f"POST request to {url} failed: {exc}")
        return None

    def _send_get_request(
        self,
        url: str,
    ) -> APIResponse:
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except JSONDecodeError:
            logging.warning(f"Failed to decode JSON from {url}")
        except requests.exceptions.RequestException as exc:
            logging.warning(f"Request to {url} failed: {exc}")
        return []

    def _get_auth_headers(self):
        return {"Api-Key": self.api_token}
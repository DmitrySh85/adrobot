import json

from django.test import TestCase

import unittest
from unittest.mock import patch, MagicMock
from keitaro_wrapper.api_manager import KeitaroAPIManager


class TestKeitaroAPIManager(TestCase):
    def setUp(self):
        self.api = KeitaroAPIManager(api_host="https://fakehost/", api_token="fake-token")
        self.sample_data = [{"id": 1, "name": "Test"}]

    # ----------------- GET Methods -----------------
    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_offers_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        offers = self.api.get_offers()
        self.assertEqual(offers, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_domains_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        domains = self.api.get_domains()
        self.assertEqual(domains, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_sources_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        sources = self.api.get_sources()
        self.assertEqual(sources, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_groups_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        groups = self.api.get_groups()
        self.assertEqual(groups, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_flow_actions_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        actions = self.api.get_flow_actions()
        self.assertEqual(actions, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_campaigns_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        campaigns = self.api.get_campaigns()
        self.assertEqual(campaigns, self.sample_data)

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_campaign_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data[0]),
            raise_for_status=MagicMock()
        )
        campaign = self.api.get_campaign(1)
        self.assertEqual(campaign, self.sample_data[0])

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_flows_success(self, mock_get):
        mock_get.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        flows = self.api.get_flows(1)
        self.assertEqual(flows, self.sample_data)

    # ----------------- POST Methods -----------------
    @patch("keitaro_wrapper.api_manager.requests.post")
    def test_create_campaign_success(self, mock_post):
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data[0]),
            raise_for_status=MagicMock()
        )
        payload = {"name": "Test"}
        response = self.api.create_campaign(payload)
        self.assertEqual(response, self.sample_data[0])

    @patch("keitaro_wrapper.api_manager.requests.post")
    def test_create_flow_success(self, mock_post):
        mock_post.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data[0]),
            raise_for_status=MagicMock()
        )
        payload = {"name": "Flow"}
        response = self.api.create_flow(payload)
        self.assertEqual(response, self.sample_data[0])

    # ----------------- PUT Methods -----------------
    @patch("keitaro_wrapper.api_manager.requests.put")
    def test_update_flow_success(self, mock_put):
        mock_put.return_value = MagicMock(
            json=MagicMock(return_value=self.sample_data),
            raise_for_status=MagicMock()
        )
        payload = {"name": "Updated Flow"}
        response = self.api.update_flow(1, payload)
        self.assertEqual(response, self.sample_data)

    # ----------------- Error Handling -----------------
    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_error_returns_empty_list(self, mock_get):
        mock_response = MagicMock()
        # raise_for_status должен выбрасывать requests.exceptions.HTTPError
        from requests.exceptions import HTTPError
        mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
        mock_response.json = MagicMock(return_value=[])
        mock_get.return_value = mock_response

        result = self.api.get_offers()
        self.assertEqual(result, [])

    @patch("keitaro_wrapper.api_manager.requests.get")
    def test_get_invalid_json_returns_empty_list(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mock_get.return_value = mock_response

        result = self.api.get_offers()
        self.assertEqual(result, [])


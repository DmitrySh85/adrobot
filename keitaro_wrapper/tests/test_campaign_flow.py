from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse

from ..models import Flow, Offer, OfferFlow


class CampaignFlowsTests(TestCase):

    @patch("keitaro_wrapper.views.KeitaroAPIManager")
    def test_flows_insert_and_offerflows(self, mock_api):
        mock_api.return_value.get_flows.return_value = [
            {
                "id": 1,
                "name": "Main",
                "type": "regular",
                "campaign_id": 123,
                "position": 0,
                "action_options": {},
                "comments": "",
                "state": "active",
                "action_type": "",
                "action_payload": "",
                "schema": "",
                "collect_clicks": False,
                "filter_or": False,
                "weight": 100,
                "offer_selection": "",
                "filters": [],
                "triggers": [],
                "landings": [],
                "offers": [
                    {"offer_id": 100, "share": 70},
                    {"offer_id": 200, "share": 30}
                ]
            }
        ]

        url = reverse("keitaro_wrapper:campaign_streams", args=[123])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Flow.objects.count(), 1)
        self.assertEqual(Offer.objects.count(), 2)
        self.assertEqual(OfferFlow.objects.count(), 2)

        of100 = OfferFlow.objects.get(offer__keitaro_offer_id=100)
        self.assertEqual(of100.share, 70)
        self.assertEqual(of100.state, "published")

        of200 = OfferFlow.objects.get(offer__keitaro_offer_id=200)
        self.assertEqual(of200.share, 30)
        self.assertEqual(of200.state, "published")

    @patch("keitaro_wrapper.views.KeitaroAPIManager")
    def test_offerflow_deleted_when_missing(self, mock_api):
        flow = Flow.objects.create(
            keitaro_flow_id=1, name="x", type="x", campaign_id=123,
            position=0, action_options={}, comments="", state="active",
            action_type="", action_payload="", schema="",
            collect_clicks=False, filter_or=False,
            weight=100, offer_selection="", filters=[],
            triggers=[], landings=[]
        )

        offer1 = Offer.objects.create(keitaro_offer_id=100, name="x")
        offer2 = Offer.objects.create(keitaro_offer_id=200, name="x")

        OfferFlow.objects.create(flow=flow, offer=offer1, share=50, state="published")
        OfferFlow.objects.create(flow=flow, offer=offer2, share=50, state="published")

        mock_api.return_value.get_flows.return_value = [
            {
                "id": 1, "name": "x", "type": "x", "campaign_id": 123,
                "position": 0, "action_options": {}, "comments": "",
                "state": "active", "action_type": "", "action_payload": "",
                "schema": "", "collect_clicks": False, "filter_or": False,
                "weight": 100, "offer_selection": "", "filters": [],
                "triggers": [], "landings": [],
                "offers": [{"offer_id": 100, "share": 50}]
            }
        ]

        url = reverse("keitaro_wrapper:campaign_streams", args=[123])
        self.client.get(url)

        deleted = OfferFlow.objects.get(offer=offer2)
        self.assertEqual(deleted.state, "deleted")
        self.assertEqual(deleted.share, 0)

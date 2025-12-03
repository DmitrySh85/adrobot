import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from ..models import Flow, Offer, OfferFlow


class FlowUpdateTests(TestCase):

    @patch("keitaro_wrapper.views.KeitaroAPIManager")
    def test_flow_update_changes_pending_add_to_published(self, mock_api):
        mock_api.return_value.update_flow.return_value = {"ok": True}

        flow = Flow.objects.create(
            keitaro_flow_id=1, name="Flow1", type="x", campaign_id=99,
            position=0, action_options={}, comments="", state="active",
            action_type="", action_payload="", schema="",
            collect_clicks=False, filter_or=False,
            weight=100, offer_selection="", filters=[],
            triggers=[], landings=[]
        )
        offer = Offer.objects.create(keitaro_offer_id=100, name="A")
        OfferFlow.objects.create(flow=flow, offer=offer, share=50, state="pending_add")

        url = reverse("keitaro_wrapper:flow_update", args=[1])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 200)

        of = OfferFlow.objects.get(offer=offer)
        self.assertEqual(of.state, "published")
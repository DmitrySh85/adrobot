import json
from django.test import TestCase
from django.urls import reverse
from ..models import Flow, Offer, OfferFlow


class OfferFlowUpdateTests(TestCase):

    def test_offer_flow_create(self):
        flow = Flow.objects.create(
            keitaro_flow_id=1, name="Flow1", type="x", campaign_id=99,
            position=0, action_options={}, comments="", state="active",
            action_type="", action_payload="", schema="",
            collect_clicks=False, filter_or=False,
            weight=100, offer_selection="", filters=[],
            triggers=[], landings=[]
        )

        data = {
            "offer_id": 777,
            "share": 80,
            "state": "pending_add",
            "is_pinned": True
        }

        url = reverse("keitaro_wrapper:flow_update_offer", args=[1])
        resp = self.client.post(url, data=json.dumps(data),
                                content_type="application/json")

        self.assertEqual(resp.status_code, 200)

        offer = Offer.objects.get(keitaro_offer_id=777)
        self.assertIsNotNone(offer)

        offerflow = OfferFlow.objects.get(offer=offer)
        self.assertEqual(offerflow.share, 80)
        self.assertEqual(offerflow.state, "pending_add")
        self.assertTrue(offerflow.is_pinned)
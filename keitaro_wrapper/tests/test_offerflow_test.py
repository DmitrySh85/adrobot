from django.test import TestCase
from django.urls import reverse
from ..models import Flow, Offer, OfferFlow


class OfferFlowsGetTests(TestCase):

    def test_offerflows_list(self):
        flow = Flow.objects.create(
            keitaro_flow_id=1, name="Flow1", type="x", campaign_id=99,
            position=0, action_options={}, comments="", state="active",
            action_type="", action_payload="", schema="",
            collect_clicks=False, filter_or=False,
            weight=100, offer_selection="", filters=[],
            triggers=[], landings=[]
        )

        offer = Offer.objects.create(keitaro_offer_id=100, name="x")
        OfferFlow.objects.create(flow=flow, offer=offer, share=10, state="published")

        url = reverse("keitaro_wrapper:offer_flows", args=[1])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()["offer_flows"]
        self.assertEqual(data[0]["offer"], 100)
        self.assertEqual(data[0]["share"], 10)
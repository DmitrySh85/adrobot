from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from ..models import Offer


class OffersTests(TestCase):

    @patch("keitaro_wrapper.views.KeitaroAPIManager")
    def test_offers_creation(self, mock_api):
        mock_api.return_value.get_offers.return_value = [
            {"id": 10, "name": "Offer A"},
            {"id": 20, "name": "Offer B"},
        ]

        url = reverse("keitaro_wrapper:offers")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(Offer.objects.filter(keitaro_offer_id=10).exists())
        self.assertTrue(Offer.objects.filter(keitaro_offer_id=20).exists())
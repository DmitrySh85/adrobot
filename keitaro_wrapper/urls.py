from django.urls import path

from .views import (
    HomeView,
    CampaignCreateView,
    CampaignEditListView,
    CampaignDetailView,
    CampaignFlowsView,
    OffersView,
    FlowUpdateView,
    OfferFlowUpdateView,
    OfferFlowsView
)

app_name = "keitaro_wrapper"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("create/", CampaignCreateView.as_view(), name="create_company"),
    path("edit/", CampaignEditListView.as_view(), name="edit_company"),
    path("edit/<int:campaign_id>/", CampaignDetailView.as_view(), name="campaign_detail"),
    path("company/<int:campaign_id>/streams/", CampaignFlowsView.as_view(), name="campaign_streams"),
    path("offers/", OffersView.as_view(), name="offers"),
    path("flow/<int:flow_id>/", FlowUpdateView.as_view(), name="flow_update"),
    path("flow/<int:flow_id>/update_offer/", OfferFlowUpdateView.as_view(), name="flow_update_offer"),
    path("flow/<int:flow_id>/offer_flows/", OfferFlowsView.as_view(), name="offer_flows"),
]

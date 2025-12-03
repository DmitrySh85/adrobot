from django.db import models


class Offer(models.Model):
    keitaro_offer_id = models.IntegerField()
    name = models.CharField(max_length=100)


class Flow(models.Model):
    keitaro_flow_id = models.IntegerField()
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    campaign_id = models.IntegerField()
    position = models.IntegerField()
    action_options = models.JSONField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=100)
    action_type = models.CharField(max_length=100)
    action_payload = models.TextField(null=True, blank=True)
    schema = models.TextField(null=True, blank=True)
    collect_clicks = models.BooleanField(default=False)
    filter_or = models.BooleanField(default=False)
    weight = models.IntegerField(default=100)
    offer_selection = models.CharField(max_length=100)
    filters = models.JSONField(default=list)
    triggers = models.JSONField(default=list)
    landings = models.JSONField(default=list)


class OfferFlow(models.Model):

    offer = models.ForeignKey(Offer, on_delete=models.PROTECT)
    flow = models.ForeignKey(Flow, on_delete=models.PROTECT)
    share = models.IntegerField()
    state = models.CharField(
        max_length=30,
        choices=[
            ("pending_add", "Подготовлен к отправке"),
            ("published", "Опубликован"),
            ("pending_delete", "Подготовлен к удалению"),
            ("deleted", "Удален"),
        ]
    )
    is_pinned = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['flow', 'offer']]
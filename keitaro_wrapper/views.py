import json

from django.db import transaction
from django.views.generic import TemplateView, FormView, View
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.text import slugify
from uuid import uuid4

from .api_manager import KeitaroAPIManager
from .forms import CampaignForm
from .models import Offer, Flow, OfferFlow


class FlowActionResolver:
    @staticmethod
    def pick(actions: list[dict] | None, schema: str) -> str:
        """Возвращает доступный action_type в зависимости от схемы."""
        fallback = "redirect" if schema == "redirect" else "offers"
        if not actions:
            return fallback

        schema_target_type = "redirect" if schema == "redirect" else "other"
        filtered = [a for a in actions if a.get("type") == schema_target_type]

        if filtered:
            return filtered[0].get("key", fallback)

        # fallback на любой action_type
        return actions[0].get("key", fallback)


class HomeView(TemplateView):
    template_name = "keitaro_wrapper/home.html"


class CampaignCreateView(FormView):
    template_name = "keitaro_wrapper/create.html"
    form_class = CampaignForm
    success_url = reverse_lazy("keitaro_wrapper:create_company")

    def get_api_data(self):
        domains = cache.get("keitaro_domains")
        offers = cache.get("keitaro_offers")
        sources = cache.get("keitaro_sources")
        groups = cache.get("keitaro_groups")
        actions = cache.get("keitaro_flow_actions")

        if not domains or not offers or not sources or groups is None or actions is None:
            api = KeitaroAPIManager()
            domains = api.get_domains()
            offers = api.get_offers()
            sources = api.get_sources()
            groups = api.get_groups()
            actions = api.get_flow_actions()

            # кладем в кеш на 10 минут
            cache.set("keitaro_domains", domains, 600)
            cache.set("keitaro_offers", offers, 600)
            cache.set("keitaro_sources", sources, 600)
            cache.set("keitaro_groups", groups, 600)
            cache.set("keitaro_flow_actions", actions, 600)

        return {
            "domains": domains,
            "offers": offers,
            "sources": sources,
            "groups": groups,
            "flow_actions": actions,
        }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        data = self.get_api_data()
        offers = data.get("offers", [])

        form.fields["offer"].choices = [(o["id"], o["name"]) for o in offers]

        return form

    def form_valid(self, form):
        cleaned = form.cleaned_data
        data = self.get_api_data()

        domain_id = self._pick_first_id(data.get("domains", []))
        traffic_source_id = self._pick_first_id(data.get("sources", []))
        group_id = self._pick_first_id(data.get("groups", []))
        offer_id = cleaned.get("offer")

        missing = []
        if not domain_id:
            missing.append("доменов")
        if not traffic_source_id:
            missing.append("источников трафика")
        if not offer_id:
            missing.append("офферов")

        if missing:
            form.add_error(
                None,
                f"Не удалось получить данные {', '.join(missing)} из Keitaro."
            )
            return self.form_invalid(form)

        selected_offer = self._find_by_id(data.get("offers", []), offer_id)
        alias = self._build_alias(cleaned["name"])

        payload = {
            "alias": alias,
            "name": cleaned["name"],
            "type": "position",
            "state": "active",
            "cookies_ttl": 24,
            "cost_type": "CPC",
            "cost_value": 0,
            "cost_auto": False,
            "domain_id": domain_id,
            "traffic_source_id": traffic_source_id,
            "notes": f"Country: {cleaned['country']}",
        }

        if group_id:
            payload["group_id"] = group_id

        api = KeitaroAPIManager()
        campaign_response = api.create_campaign(payload)

        if not campaign_response:
            form.add_error(None, "Не удалось создать кампанию в Keitaro. Проверьте журнал ошибок.")
            return self.form_invalid(form)

        campaign_id = campaign_response.get("id")
        if not campaign_id:
            form.add_error(None, "Keitaro вернул пустой идентификатор кампании.")
            return self.form_invalid(form)

        flow_actions = data.get("flow_actions") or []

        flow_errors = self._create_default_flows(
            api=api,
            campaign_id=int(campaign_id),
            country_code=cleaned["country"],
            offer_id=int(offer_id),
            offer_name=selected_offer["name"] if selected_offer else "",
            actions=flow_actions,
        )

        if flow_errors:
            messages.warning(
                self.request,
                "Кампания создана, но возникли ошибки при создании потоков: "
                + ", ".join(flow_errors),
            )
        else:
            messages.success(self.request, f"Кампания «{campaign_response.get('name', cleaned['name'])}» создана.")

        return super().form_valid(form)

    @staticmethod
    def _pick_first_id(items):
        return items[0]["id"] if items else None

    @staticmethod
    def _find_by_id(items, target_id):
        if not target_id:
            return None
        target_id = int(target_id)
        for item in items or []:
            if item.get("id") == target_id:
                return item
        return None

    @staticmethod
    def _build_alias(name: str) -> str:
        slug = slugify(name, allow_unicode=True)
        if slug:
            return slug
        return f"campaign-{uuid4().hex[:8]}"

    def _create_default_flows(
        self,
        api: KeitaroAPIManager,
        campaign_id: int,
        country_code: str,
        offer_id: int,
        offer_name: str = "",
        actions: list[dict] | None = None,
    ) -> list[str]:
        """Создаёт два потока: георедирект и поток с оффером."""
        errors: list[str] = []
        flows = [
            self._build_geo_redirect_flow(campaign_id, country_code, actions),
            self._build_offer_flow(campaign_id, offer_id, offer_name, actions),
        ]

        for flow in flows:
            response = api.create_flow(flow)
            if not response:
                errors.append(flow.get("name", "flow"))

        return errors

    @staticmethod
    def _build_geo_redirect_flow(campaign_id: int, country_code: str, actions: list[dict] | None) -> dict:
        redirect_action = FlowActionResolver.pick(actions, schema="redirect")
        return {
            "campaign_id": campaign_id,
            "schema": "redirect",
            "type": "forced",
            "name": f"{campaign_id}-geo-redirect",
            "action_type": redirect_action,
            "action_options": {"url": "https://www.google.com"},
            "comments": "Auto-generated redirect for selected country",
            "state": "active",
            "collect_clicks": False,
            "filter_or": False,
            "filters": [
                {
                    "name": "country",
                    "mode": "accept",
                    "payload": [country_code],
                }
            ],
        }

    @staticmethod
    def _build_offer_flow(
        campaign_id: int,
        offer_id: int,
        offer_name: str,
        actions: list[dict] | None,
    ) -> dict:
        offer_action = FlowActionResolver.pick(actions, schema="landings")
        return {
            "campaign_id": campaign_id,
            "schema": "landings",
            "type": "default",
            "name": f"{campaign_id}-offer",
            "action_type": offer_action,
            "comments": f"Auto flow for offer {offer_name or offer_id}",
            "state": "active",
            "collect_clicks": False,
            "filter_or": False,
            "offers": [
                {
                    "offer_id": offer_id,
                    "share": 100,
                    "state": "active",
                }
            ],
        }

class CampaignEditListView(TemplateView):
    template_name = "keitaro_wrapper/edit_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api = KeitaroAPIManager()
        context["campaigns"] = api.get_campaigns()
        return context


class CampaignDetailView(TemplateView):
    template_name = "keitaro_wrapper/campaign_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign_id = kwargs.get("campaign_id")
        api = KeitaroAPIManager()
        context["campaign"] = api.get_campaign(campaign_id)
        return context


class CampaignFlowsView(View):
    def get(self, request, campaign_id: int):
        # Получаем данные из API
        flows = self._get_flows_from_api(campaign_id)

        # Сохраняем потоки в БД
        self._sync_flows_to_db(flows)

        # Синхронизируем офферы для каждого потока
        for flow_json in flows:
            self._sync_flow_offers(flow_json)

        return JsonResponse({"flows": flows})

    def _get_flows_from_api(self, campaign_id: int) -> list:
        """Получает потоки из API Keitaro и фильтрует те, у которых есть офферы"""
        api = KeitaroAPIManager()
        flows = api.get_flows(campaign_id)
        return [flow for flow in flows if flow["offers"]]

    def _sync_flows_to_db(self, flows: list) -> None:
        """Синхронизирует потоки с базой данных"""
        incoming_ids = [f["id"] for f in flows]

        # Получаем существующие ID потоков
        existing_flow_ids = self._get_existing_flow_ids(incoming_ids)

        # Создаем новые потоки
        flows_to_insert = self._prepare_flows_for_insertion(flows, existing_flow_ids)

        # Массово создаем записи
        if flows_to_insert:
            Flow.objects.bulk_create(flows_to_insert, ignore_conflicts=True)

    def _get_existing_flow_ids(self, flow_ids: list) -> set:
        """Возвращает set существующих ID потоков"""
        return set(
            Flow.objects.filter(keitaro_flow_id__in=flow_ids)
            .values_list("keitaro_flow_id", flat=True)
        )

    def _prepare_flows_for_insertion(self, flows: list, existing_flow_ids: set) -> list:
        """Подготавливает объекты Flow для вставки"""
        return [
            Flow(
                keitaro_flow_id=f["id"],
                name=f["name"],
                type=f["type"],
                campaign_id=f["campaign_id"],
                position=f["position"],
                action_options=f["action_options"],
                comments=f["comments"],
                state=f["state"],
                action_type=f["action_type"],
                action_payload=f["action_payload"],
                schema=f["schema"],
                collect_clicks=f["collect_clicks"],
                filter_or=f["filter_or"],
                weight=f["weight"],
                offer_selection=f["offer_selection"],
                filters=f["filters"],
                triggers=f["triggers"],
                landings=f["landings"]
            )
            for f in flows
            if f["id"] not in existing_flow_ids
        ]

    def _sync_flow_offers(self, flow_json: dict) -> None:
        """Синхронизирует офферы для конкретного потока"""
        flow = self._get_flow_instance(flow_json)
        if not flow:
            return

        # Подготавливаем данные об офферах
        incoming_offers = self._prepare_incoming_offers(flow_json)
        incoming_offer_ids = set(incoming_offers.keys())

        # Получаем существующие связи офферов с потоком
        existing_offerflows = OfferFlow.objects.filter(flow=flow)
        existing_offer_ids = set(
            existing_offerflows.values_list("offer__keitaro_offer_id", flat=True)
        )

        # Добавляем новые офферы
        self._add_new_offers(flow, incoming_offers, incoming_offer_ids, existing_offer_ids)

        # Обновляем существующие офферы
        self._update_existing_offers(flow, incoming_offers, incoming_offer_ids, existing_offer_ids)

        # Удаляем отсутствующие офферы
        self._delete_missing_offers(flow, incoming_offer_ids, existing_offer_ids)

        # Восстанавливаем ранее удаленные офферы
        self._restore_deleted_offers(flow, incoming_offers, incoming_offer_ids)

    def _get_flow_instance(self, flow_json: dict):
        """Возвращает экземпляр Flow по ID из JSON"""
        try:
            return Flow.objects.get(keitaro_flow_id=flow_json["id"])
        except Flow.DoesNotExist:
            return None

    def _prepare_incoming_offers(self, flow_json: dict) -> dict:
        """Преобразует список офферов в словарь для быстрого доступа"""
        return {
            o["offer_id"]: o
            for o in flow_json.get("offers", [])
        }

    def _add_new_offers(self, flow: Flow, incoming_offers: dict,
                        incoming_offer_ids: set, existing_offer_ids: set) -> None:
        """Добавляет новые офферы в поток"""
        missing_offer_ids = incoming_offer_ids - existing_offer_ids
        if not missing_offer_ids:
            return

        new_offerflows = []
        for offer_id in missing_offer_ids:
            offer, _ = Offer.objects.get_or_create(
                keitaro_offer_id=offer_id,
                defaults={"name": f"offer #{offer_id}"}
            )
            share = incoming_offers[offer_id].get("share", 0)
            new_offerflows.append(
                OfferFlow(
                    offer=offer,
                    flow=flow,
                    share=share,
                    state="published",
                    is_pinned=False
                )
            )

        OfferFlow.objects.bulk_create(new_offerflows)

    def _update_existing_offers(self, flow: Flow, incoming_offers: dict,
                                incoming_offer_ids: set, existing_offer_ids: set) -> None:
        """Обновляет существующие связи офферов с потоком"""
        common_offer_ids = incoming_offer_ids & existing_offer_ids
        if not common_offer_ids:
            return

        existing_offerflows = OfferFlow.objects.filter(flow=flow)
        updates = []

        for offerflow in existing_offerflows:
            offer_id = offerflow.offer.keitaro_offer_id
            if offer_id in common_offer_ids:
                new_share = incoming_offers[offer_id].get("share", 0)
                if offerflow.share != new_share or offerflow.state != "published":
                    offerflow.share = new_share
                    offerflow.state = "published"
                    updates.append(offerflow)

        if updates:
            OfferFlow.objects.bulk_update(updates, ["share", "state", "updated_at"])

    def _delete_missing_offers(self, flow: Flow, incoming_offer_ids: set,
                               existing_offer_ids: set) -> None:
        """Помечает отсутствующие офферы как удаленные"""
        to_delete = existing_offer_ids - incoming_offer_ids
        if not to_delete:
            return

        OfferFlow.objects.filter(
            flow=flow,
            offer__keitaro_offer_id__in=to_delete,
            state="published"
        ).update(state="deleted", share=0)

    def _restore_deleted_offers(self, flow: Flow, incoming_offers: dict,
                                incoming_offer_ids: set) -> None:
        """Восстанавливает ранее удаленные офферы"""
        restored_offerflows = OfferFlow.objects.filter(
            flow=flow,
            offer__keitaro_offer_id__in=incoming_offer_ids,
            state__in=["pending_delete", "deleted"]
        )

        updates = []
        for offerflow in restored_offerflows:
            offer_id = offerflow.offer.keitaro_offer_id
            new_share = incoming_offers[offer_id].get("share", 0)
            if offerflow.share != new_share or offerflow.state != "published":
                offerflow.share = new_share
                offerflow.state = "published"
                updates.append(offerflow)

        if updates:
            OfferFlow.objects.bulk_update(updates, ["share", "state", "updated_at"])


class OffersView(View):
    def get(self, request):
        api = KeitaroAPIManager()
        offers = api.get_offers()

        incoming_ids = [o["id"] for o in offers]

        # какие уже есть в БД
        existing_ids = set(
            Offer.objects.filter(keitaro_offer_id__in=incoming_ids)
                         .values_list("keitaro_offer_id", flat=True)
        )

        # какие нужно вставить
        to_insert = [
            Offer(
                keitaro_offer_id=o["id"],
                name=o["name"]
            )
            for o in offers
            if o["id"] not in existing_ids
        ]

        # массовая вставка за один SQL запрос
        Offer.objects.bulk_create(to_insert, ignore_conflicts=True)
        return JsonResponse({"offers": offers})


class FlowUpdateView(View):
    @transaction.atomic
    def put(self, request, flow_id: int):
        # Получаем локальный Flow
        try:
            flow = Flow.objects.get(keitaro_flow_id=flow_id)
        except Flow.DoesNotExist:
            return JsonResponse({"error": "Flow not found"}, status=404)

        # ================= Сборка payload =================
        # Только офферы, которые нужно отправить
        offerflows = OfferFlow.objects.filter(
            flow=flow,
            state__in=["pending_add", "published"]
        )
        offers_payload = [
            {
                "offer_id": of.offer.keitaro_offer_id,
                "share": of.share,
                "state": "active"
            }
            for of in offerflows
        ]

        # Собираем полный payload для Keitaro
        payload = {
            "id": flow.keitaro_flow_id,
            "name": flow.name,
            "type": flow.type,
            "campaign_id": flow.campaign_id,
            "position": flow.position,
            "action_options": flow.action_options,
            "comments": flow.comments,
            "state": flow.state,
            "action_type": flow.action_type,
            "action_payload": flow.action_payload,
            "schema": flow.schema,
            "collect_clicks": flow.collect_clicks,
            "filter_or": flow.filter_or,
            "weight": flow.weight,
            "offer_selection": flow.offer_selection,
            "filters": flow.filters,
            "triggers": flow.triggers,
            "landings": flow.landings,
            "offers": offers_payload
        }

        # ================= Отправка в Keitaro =================
        api = KeitaroAPIManager()
        try:
            updated_flow = api.update_flow(flow_id, payload)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        # ================= Обновление локальных OfferFlow =================
        OfferFlow.objects.filter(flow=flow, state="pending_add").update(state="published")
        OfferFlow.objects.filter(flow=flow, state="pending_delete").update(state="deleted")
        return JsonResponse({"flow": updated_flow})


class OfferFlowUpdateView(View):

    @transaction.atomic
    def post(self, request, flow_id: int):

        try:
            data = json.loads(request.body)
            offer_id = data["offer_id"]
            share = data.get("share", 0)
            state = data.get("state", "pending_add")
            is_pinned = data.get("is_pinned", False)
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid payload"}, status=400)

        # Получаем объекты Flow и Offer
        try:
            flow = Flow.objects.get(keitaro_flow_id=flow_id)
        except Flow.DoesNotExist:
            return JsonResponse({"error": "Flow not found"}, status=404)

        offer, _ = Offer.objects.get_or_create(
            keitaro_offer_id=offer_id,
            defaults={"name": f"offer #{offer_id}"}
        )

        # Создаём или обновляем OfferFlow
        offerflow, created = OfferFlow.objects.get_or_create(
            flow=flow,
            offer=offer,
            defaults={
                "share": share,
                "state": state,
                "is_pinned": is_pinned
            }
        )

        if not created:
            # Обновляем существующий
            offerflow.share = share
            offerflow.state = state
            offerflow.is_pinned = is_pinned
            offerflow.save()
        return JsonResponse({
            "flow_id": flow.keitaro_flow_id,
            "offer_id": offer.keitaro_offer_id,
            "share": offerflow.share,
            "state": offerflow.state,
            "is_pinned": offerflow.is_pinned
        })


class OfferFlowsView(View):
    def get(self, request, flow_id: int):
        offer_flows = OfferFlow.objects.filter(flow__keitaro_flow_id=flow_id).prefetch_related(
            "offer", "flow"
        )
        return JsonResponse(
            {"offer_flows": [
                {
                "offer": of.offer.keitaro_offer_id,
                "flow": of.flow.keitaro_flow_id,
                "share": of.share,
                "state": of.state,
                "is_pinned": of.is_pinned
                }
            for of in offer_flows]
                  }
            )
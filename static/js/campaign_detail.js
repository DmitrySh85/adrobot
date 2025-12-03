document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const fetchBtn = document.getElementById('fetch-streams-btn');
    const flowsOutput = document.getElementById('flows-output');

    if (!fetchBtn) {
        console.error('❌ #fetch-streams-btn не найден');
        return;
    }

    // === URL из data-атрибутов ===
    const requiredAttrs = [
        'url',                   // campaign_streams → /company/<id>/streams/
        'offersUrl',             // offers → /offers/
        'flowUpdateUrl',         // flow_update → /flow/0/
        'offerUpdateUrlTemplate',// flow_update_offer → /flow/0/update_offer/
        'offerFlowsUrlTemplate'  // offer_flows → /flow/0/offer_flows/
    ];

    const urls = {};
    for (const attr of requiredAttrs) {
        const val = fetchBtn.dataset[attr];
        if (!val) {
            const msg = `❌ data-${attr} не задан в HTML`;
            console.error(msg);
            flowsOutput.innerHTML = `<p class="error">${msg}</p>`;
            return;
        }
        urls[attr] = val;
        console.log(`✅ data-${attr}:`, val);
    }

    let offers = {}; // { id: { id, name } }
    let flows = [];  // [flow]

    const STATUS_ICONS = {
        pending_add: '🆕',
        published: '✅',
        pending_delete: '🔄',
        deleted: '🗑️'
    };

    const fmtStatus = (s) => STATUS_ICONS[s] || s;

    // === Пересчёт долей (с поддержкой pinned и неактивных) ===
    function recalculateShares(flowData) {
        const active = flowData.offerFlows.filter(of =>
            of.state === 'published' || of.state === 'pending_add'
        );
        const pinned = active.filter(of => of.is_pinned);
        const unpinned = active.filter(of => !of.is_pinned);

        const pinnedSum = pinned.reduce((sum, of) => sum + of.share, 0);
        const remaining = Math.max(0, 100 - pinnedSum);

        // Неактивные → доля = 0
        flowData.offerFlows
            .filter(of => !active.includes(of))
            .forEach(of => of.share = 0);

        if (unpinned.length === 0) {
            if (pinned.length > 0) {
                const base = Math.floor(100 / pinned.length);
                let rem = 100 % pinned.length;
                pinned.forEach((of, i) => of.share = base + (i < rem ? 1 : 0));
            }
            return;
        }

        const base = Math.floor(remaining / unpinned.length);
        let rem = remaining % unpinned.length;
        unpinned.forEach((of, i) => of.share = base + (i < rem ? 1 : 0));
    }

    // === Синхронизация одного OfferFlow с бэком ===
    async function syncOfferFlow(flowId, offerId, payload) {
        const url = urls.offerUpdateUrlTemplate.replace('/0/', `/${flowId}/`);
        console.log(`📡 POST ${url}`, { offer_id: offerId, ...payload });

        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ offer_id: offerId, ...payload })
        });

        if (!res.ok) {
            const errText = await res.text();
            let err = { message: errText };
            try { err = JSON.parse(errText); } catch {}
            throw new Error(err.error || err.message || `HTTP ${res.status}`);
        }

        return await res.json();
    }

    // === Рендеринг UI ===
    function render() {
        if (flows.length === 0) {
            flowsOutput.innerHTML = '<p>Нажмите «Получить потоки из Keitaro».</p>';
            return;
        }

        const html = flows.map(flow => {
            const rows = flow.offerFlows.map(of => {
                const offer = offers[of.offer_id] || { name: `Offer #${of.offer_id}` };
                const isInactive = of.state === 'pending_delete' || of.state === 'deleted';
                const rowClass = isInactive ? 'offer-row-inactive' : 'offer-row';

                const actionBtn = of.state === 'pending_delete' || of.state === 'deleted'
                    ? `<button class="btn-sm btn-return" data-flow="${flow.id}" data-offer="${of.offer_id}">↩️ Вернуть</button>`
                    : `<button class="btn-sm btn-delete" data-flow="${flow.id}" data-offer="${of.offer_id}">🗑️ Удалить</button>`;

                return `
                    <tr class="${rowClass}">
                        <td>${isInactive ? `<s>${offer.name}</s>` : offer.name} (${of.offer_id})</td>
                        <td>${of.share}</td>
                        <td>
                            <span class="status-badge">${fmtStatus(of.state)}</span>
                            ${of.state}
                        </td>
                        <td>
                            <button class="btn-sm btn-pin"
                                    data-flow="${flow.id}"
                                    data-offer="${of.offer_id}"
                                    title="${of.is_pinned ? 'Открепить' : 'Прикрепить'}">
                                ${of.is_pinned ? '📌' : '📎'}
                            </button>
                            ${actionBtn}
                        </td>
                    </tr>
                `;
            }).join('');

            return `
                <div class="flow-card" data-flow-id="${flow.id}">
                    <h3>Flow: ${flow.name || '—'} (ID: ${flow.id})</h3>
                    <p>Тип: ${flow.type}</p>

                    <!-- ✅ БЛОК ДОБАВЛЕНИЯ ОФФЕРА -->
                    <div class="add-offer-control">
                        <input type="text" class="offer-search"
                               placeholder="Добавить оффер (по ID или названию)…"
                               data-flow-id="${flow.id}"
                               autocomplete="off">
                        <div class="offer-suggestions" style="display:none;"></div>
                    </div>

                    <div class="flow-actions">
                        <button class="btn btn-push" data-id="${flow.id}">📤 Отправить в Keitaro</button>
                        <button class="btn btn-reload" data-id="${flow.id}">🔄 Обновить</button>
                    </div>

                    <table class="offers-table">
                        <thead>
                            <tr>
                                <th>Оффер</th>
                                <th>Доля</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            `;
        }).join('');

        flowsOutput.innerHTML = html;
        initOfferAutocomplete();
    }

    // === АВТОКОМПЛИТ ДЛЯ ОФФЕРОВ ===
    let offerSearchTimeout = null;

    function initOfferAutocomplete() {
        document.querySelectorAll('.offer-search').forEach(input => {
            input.addEventListener('input', function() {
                const query = this.value.trim().toLowerCase();
                const flowId = parseInt(this.dataset.flowId);
                const suggestionsEl = this.nextElementSibling;

                clearTimeout(offerSearchTimeout);
                if (!query) {
                    suggestionsEl.style.display = 'none';
                    return;
                }

                offerSearchTimeout = setTimeout(() => {
                    const matches = Object.values(offers)
                        .filter(o =>
                            o.id.toString().includes(query) ||
                            o.name.toLowerCase().includes(query)
                        )
                        .slice(0, 10);

                    if (matches.length === 0) {
                        suggestionsEl.style.display = 'none';
                        return;
                    }

                    suggestionsEl.innerHTML = matches.map(o => `
                        <div class="offer-suggestion-item"
                             data-offer-id="${o.id}"
                             data-flow-id="${flowId}">
                            <strong>${o.id}</strong> — ${o.name}
                        </div>
                    `).join('');
                    suggestionsEl.style.display = 'block';
                }, 200);
            });

            input.addEventListener('blur', function() {
                setTimeout(() => {
                    this.nextElementSibling.style.display = 'none';
                }, 150);
            });
        });

        // Делегирование: выбор оффера
        flowsOutput.addEventListener('click', function(e) {
            const item = e.target.closest('.offer-suggestion-item');
            if (!item) return;

            const offerId = parseInt(item.dataset.offerId);
            const flowId = parseInt(item.dataset.flowId);
            const input = item.closest('.add-offer-control').querySelector('.offer-search');

            input.value = '';
            item.parentElement.style.display = 'none';

            addOfferToFlow(flowId, offerId);
        });
    }

    // ✅ ДОБАВИТЬ ОФФЕР В FLOW
    async function addOfferToFlow(flowId, offerId) {
        const flow = flows.find(f => f.id === flowId);
        if (!flow) return;

        if (flow.offerFlows.some(of => of.offer_id === offerId)) {
            alert('⚠️ Этот оффер уже добавлен');
            return;
        }

        const prevStateMap = new Map(flow.offerFlows.map(of => [of.offer_id, { ...of }]));

        try {
            // Добавляем новый
            flow.offerFlows.push({
                offer_id: offerId,
                flow_id: flowId,
                share: 0,
                state: 'pending_add',
                is_pinned: false
            });

            recalculateShares(flow);

            const changed = flow.offerFlows.filter(of => {
                const prev = prevStateMap.get(of.offer_id);
                return !prev || of.share !== prev.share || of.state !== prev.state || of.is_pinned !== prev.is_pinned;
            });

            render();
            await Promise.all(changed.map(of =>
                syncOfferFlow(flowId, of.offer_id, {
                    share: of.share,
                    state: of.state,
                    is_pinned: of.is_pinned
                })
            ));
            console.log(`✅ Оффер ${offerId} добавлен в Flow ${flowId}`);
        } catch (err) {
            // Откат
            flow.offerFlows = Array.from(prevStateMap.values());
            recalculateShares(flow);
            render();
            alert(`⚠️ ${err.message}`);
        }
    }

    // === ОБРАБОТЧИКИ КНОПОК ===
    flowsOutput.addEventListener('click', async (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;

        if (btn.classList.contains('btn-push')) {
            const flowId = parseInt(btn.dataset.id);
            if (!flowId) return;

            const url = urls.flowUpdateUrl.replace('/0/', `/${flowId}/`);
            try {
                const res = await fetch(url, {
                    method: 'PUT',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                const data = await res.json();

                if (res.ok) {
                    const flow = flows.find(f => f.id === flowId);
                    if (flow) {
                        flow.offerFlows.forEach(of => {
                            if (of.state === 'pending_add') of.state = 'published';
                            if (of.state === 'pending_delete') of.state = 'deleted';
                        });
                        render();
                    }
                    alert(`✅ Flow ${flowId} отправлен в Keitaro`);
                } else {
                    alert(`❌ ${data.error || res.statusText}`);
                }
            } catch (err) {
                console.error(err);
                alert(`⚠️ ${err.message}`);
            }
        }
        else if (btn.classList.contains('btn-reload')) {
            // ✅ «Обновить» = полная синхронизация через CampaignFlowsView
            await loadAllFlows();
        }
        else {
            // OfferFlow-действия (удалить/вернуть/прикрепить)
            const flowId = parseInt(btn.dataset.flow);
            const offerId = parseInt(btn.dataset.offer);
            if (!flowId || isNaN(offerId)) return;

            const flow = flows.find(f => f.id === flowId);
            const targetOf = flow?.offerFlows.find(x => x.offer_id === offerId);
            if (!flow || !targetOf) return;

            const prevStateMap = new Map(flow.offerFlows.map(of => [of.offer_id, { ...of }]));

            try {
                if (btn.classList.contains('btn-delete')) {
                    if (targetOf.state !== 'published') return;
                    targetOf.state = 'pending_delete';
                    targetOf.share = 0;
                }
                else if (btn.classList.contains('btn-return')) {
                    if (!['pending_delete', 'deleted'].includes(targetOf.state)) return;
                    targetOf.state = 'pending_add';
                }
                else if (btn.classList.contains('btn-pin')) {
                    targetOf.is_pinned = !targetOf.is_pinned;
                }
                else return;

                recalculateShares(flow);

                const changed = flow.offerFlows.filter(of => {
                    const prev = prevStateMap.get(of.offer_id);
                    return !prev || of.share !== prev.share || of.state !== prev.state || of.is_pinned !== prev.is_pinned;
                });

                if (changed.length === 0) { render(); return; }

                render();
                await Promise.all(changed.map(of =>
                    syncOfferFlow(flowId, of.offer_id, {
                        share: of.share,
                        state: of.state,
                        is_pinned: of.is_pinned
                    })
                ));
            } catch (err) {
                // Откат
                flow.offerFlows.forEach(of => {
                    const prev = prevStateMap.get(of.offer_id);
                    if (prev) Object.assign(of, prev);
                });
                recalculateShares(flow);
                render();
                alert(`⚠️ ${err.message}`);
            }
        }
    });

    // === ЗАГРУЗКА ДАННЫХ ИЗ KEITARO ===
    async function loadAllFlows() {
        flowsOutput.innerHTML = '<p>🔄 Синхронизация с Keitaro…</p>';

        try {
            // 1. Получаем офферы
            const offersRes = await fetch(urls.offersUrl);
            if (!offersRes.ok) throw new Error(`Offers: ${offersRes.status}`);
            const offersData = await offersRes.json();
            offers = Object.fromEntries(offersData.offers.map(o => [o.id, o]));

            // 2. Синхронизируем потоки и OfferFlow через CampaignFlowsView
            const streamsRes = await fetch(urls.url);
            if (!streamsRes.ok) throw new Error(`Streams: ${streamsRes.status}`);
            const streamsData = await streamsRes.json();

            // 3. Для каждого flow — получаем актуальные OfferFlow из БД
            flows = [];
            for (const ktFlow of streamsData.flows) {
                const ofUrl = urls.offerFlowsUrlTemplate.replace('/0/', `/${ktFlow.id}/`);
                const ofRes = await fetch(ofUrl);
                const ofData = ofRes.ok ? await ofRes.json() : { offer_flows: [] };

                const flow = {
                    id: ktFlow.id,
                    name: ktFlow.name,
                    type: ktFlow.type,
                    offerFlows: ofData.offer_flows.map(of => ({
                        offer_id: of.offer,
                        flow_id: of.flow,
                        share: of.share,
                        state: of.state,
                        is_pinned: of.is_pinned
                    }))
                };

                recalculateShares(flow);
                flows.push(flow);
            }

            render();
        } catch (err) {
            console.error('❌ loadAllFlows error:', err);
            flowsOutput.innerHTML = `<p class="error">❌ ${err.message}</p>`;
        }
    }

    fetchBtn.addEventListener('click', loadAllFlows);
});
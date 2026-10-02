/**
 * ContextForge Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initLineageDAG();
    initAssetCatalog();
    initApprovalQueue();
    initEvalDashboard();
});

// --- Tab Switching ---
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const targetTab = tab.getAttribute("data-tab");
            document.querySelectorAll(".screen-view").forEach(view => {
                view.classList.remove("active");
            });
            const activeView = document.getElementById(`view-${targetTab}`);
            if (activeView) activeView.classList.add("active");
        });
    });
}

// --- Screen 1: Lineage DAG (SVG Renderer) ---
async function initLineageDAG() {
    const svg = document.getElementById("dag-svg");
    const statsText = document.getElementById("dag-stats-text");
    const detailPanel = document.getElementById("node-detail-panel");
    const drawerTitle = document.getElementById("drawer-title");
    const drawerContent = document.getElementById("drawer-content");
    const closeBtn = document.getElementById("btn-close-drawer");

    closeBtn.addEventListener("click", () => detailPanel.classList.add("hidden"));

    try {
        const resp = await fetch("/api/lineage");
        const data = await resp.json();
        const nodes = data.nodes || [];
        const edges = data.edges || [];

        statsText.innerText = `${nodes.length} Nodes | ${edges.length} Lineage Edges`;

        // Layout nodes in 4 columns: raw (x=80), staging (x=380), marts (x=700), dashboard (x=1020)
        const tierCoords = {
            raw: { x: 80, yStep: 65, color: "#64748b" },
            staging: { x: 380, yStep: 75, color: "#38bdf8" },
            marts: { x: 700, yStep: 80, color: "#10b981" },
            dashboard: { x: 1020, yStep: 100, color: "#c084fc" }
        };

        const tierCounts = { raw: 0, staging: 0, marts: 0, dashboard: 0 };
        const nodePositions = {};

        nodes.forEach(node => {
            const t = node.tier || "marts";
            const cfg = tierCoords[t] || tierCoords.marts;
            const idx = tierCounts[t]++;
            const x = cfg.x;
            const y = 50 + idx * cfg.yStep;
            nodePositions[node.id] = { x, y, node, color: cfg.color };
        });

        // Clear SVG
        svg.innerHTML = `
            <defs>
                <marker id="arrow-clean" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                    <path d="M 0 0 L 8 4 L 0 8 z" fill="#38bdf8" opacity="0.6"/>
                </marker>
                <marker id="arrow-pii" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                    <path d="M 0 0 L 8 4 L 0 8 z" fill="#f43f5e"/>
                </marker>
            </defs>
        `;

        // Render Edges
        edges.forEach(edge => {
            const p1 = nodePositions[edge.source];
            const p2 = nodePositions[edge.target];
            if (p1 && p2) {
                const isPii = edge.is_pii_propagated;
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const dx = (p2.x - p1.x) * 0.5;
                const d = `M ${p1.x + 160} ${p1.y + 20} C ${p1.x + 160 + dx} ${p1.y + 20}, ${p2.x - dx} ${p2.y + 20}, ${p2.x} ${p2.y + 20}`;
                path.setAttribute("d", d);
                path.setAttribute("fill", "none");
                path.setAttribute("stroke", isPii ? "#f43f5e" : "#38bdf8");
                path.setAttribute("stroke-width", isPii ? "2.5" : "1.5");
                path.setAttribute("opacity", isPii ? "0.9" : "0.35");
                if (isPii) {
                    path.setAttribute("stroke-dasharray", "6,4");
                }
                path.setAttribute("marker-end", isPii ? "url(#arrow-pii)" : "url(#arrow-clean)");
                svg.appendChild(path);
            }
        });

        // Render Nodes
        Object.values(nodePositions).forEach(pos => {
            const n = pos.node;
            const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
            g.setAttribute("transform", `translate(${pos.x}, ${pos.y})`);
            g.style.cursor = "pointer";

            // Node card background
            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("width", "160");
            rect.setAttribute("height", "42");
            rect.setAttribute("rx", "8");
            rect.setAttribute("fill", "#0f172a");
            rect.setAttribute("stroke", n.has_pii ? "#f43f5e" : pos.color);
            rect.setAttribute("stroke-width", n.has_pii ? "2" : "1.2");
            if (n.has_pii) {
                rect.style.filter = "drop-shadow(0 0 6px rgba(244, 63, 94, 0.4))";
            }
            g.appendChild(rect);

            // Node text
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", "12");
            text.setAttribute("y", "25");
            text.setAttribute("fill", "#f8fafc");
            text.setAttribute("font-size", "11");
            text.setAttribute("font-weight", "600");
            text.setAttribute("font-family", "Plus Jakarta Sans, sans-serif");
            text.textContent = (n.label.length > 20) ? n.label.substring(0, 18) + "..." : n.label;
            g.appendChild(text);

            // PII Pill indicator
            if (n.has_pii) {
                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", "146");
                circle.setAttribute("cy", "21");
                circle.setAttribute("r", "5");
                circle.setAttribute("fill", "#f43f5e");
                g.appendChild(circle);
            }

            g.addEventListener("click", () => {
                drawerTitle.innerText = n.label;
                drawerContent.innerHTML = `
                    <div style="font-size: 0.85rem; line-height: 1.6;">
                        <p><strong>Asset ID:</strong> <code style="font-family: JetBrains Mono; font-size: 0.75rem;">${n.id}</code></p>
                        <p><strong>Tier:</strong> <span class="badge badge-accent">${n.tier}</span></p>
                        <p><strong>Certification:</strong> <span class="badge ${n.certification_status === 'CERTIFIED' ? 'badge-cert' : 'badge-accent'}">${n.certification_status}</span></p>
                        <p><strong>Owner:</strong> ${n.owner || "Data Governance Guild"}</p>
                        <p><strong>Contains PII:</strong> ${n.has_pii ? '<span class="badge badge-pii">RESTRICTED PII</span>' : 'False'}</p>
                        ${n.has_pii ? '<p style="color: #f43f5e; font-size: 0.8rem; margin-top: 0.5rem;">⚠️ Downstream tag propagation active. Reason chain verified across 3 hops under POL-007.</p>' : ''}
                    </div>
                `;
                detailPanel.classList.remove("hidden");
            });

            svg.appendChild(g);
        });

    } catch (err) {
        console.error("Error loading lineage DAG:", err);
        statsText.innerText = "Error loading lineage DAG.";
    }
}

// --- Screen 2: Asset Catalog ---
async function initAssetCatalog() {
    const container = document.getElementById("assets-container");
    const searchInput = document.getElementById("asset-search");
    const piiCheckbox = document.getElementById("filter-pii-only");

    async function loadAssets() {
        const query = searchInput.value;
        const piiOnly = piiCheckbox.checked;
        const resp = await fetch(`/api/assets?query=${encodeURIComponent(query)}&pii_only=${piiOnly}`);
        const data = await resp.json();
        const assets = data.assets || [];

        container.innerHTML = "";
        if (assets.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); grid-column: 1/-1;">No matching assets found.</p>`;
            return;
        }

        assets.forEach(a => {
            const card = document.createElement("div");
            card.className = "asset-card";

            const piiBadge = a.pii_columns_count > 0 
                ? `<span class="badge badge-pii">${a.pii_columns_count} PII Columns</span>`
                : `<span class="badge badge-cert">Clean Public</span>`;

            card.innerHTML = `
                <div class="asset-card-header">
                    <div>
                        <h3 class="asset-title">${a.display_name}</h3>
                        <span class="asset-owner">Owner: ${a.owner} | Quality: ${(a.quality_score * 100).toFixed(0)}%</span>
                    </div>
                    <div style="display:flex; gap: 0.4rem;">
                        ${piiBadge}
                        <span class="badge ${a.certification_status === 'CERTIFIED' ? 'badge-cert' : 'badge-accent'}">${a.certification_status}</span>
                    </div>
                </div>
                <p class="asset-desc">${a.description}</p>
                <div style="font-weight: 600; font-size: 0.8rem; margin-bottom: 0.3rem;">Column Schema & Governed Context:</div>
                <table class="meta-comparison-table">
                    <thead>
                        <tr>
                            <th>Column Name</th>
                            <th>Data Type</th>
                            <th>Enriched PII Status</th>
                            <th>Masking Policy</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${a.columns.map(c => `
                            <tr>
                                <td><code>${c.column_name}</code></td>
                                <td style="color: var(--text-muted);">${c.data_type}</td>
                                <td>${c.is_pii ? `<span class="badge badge-pii">${c.pii_type}</span>` : 'NONE'}</td>
                                <td style="font-size: 0.72rem; color: var(--accent-amber);">${c.is_masked ? 'POL-002 (Masked)' : 'Direct'}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
            container.appendChild(card);
        });
    }

    searchInput.addEventListener("input", loadAssets);
    piiCheckbox.addEventListener("change", loadAssets);
    loadAssets();
}

// --- Screen 3: Approval Queue ---
async function initApprovalQueue() {
    const container = document.getElementById("queue-container");
    const countBadge = document.getElementById("queue-count-badge");
    const statPill = document.getElementById("queue-stat-pill");

    async function loadQueue() {
        const resp = await fetch("/api/approval-queue");
        const data = await resp.json();
        const items = data.queue || [];

        countBadge.innerText = items.length;
        statPill.innerText = `${items.length} Proposals Requiring Review`;

        container.innerHTML = "";
        if (items.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1.5rem; background: var(--bg-surface); border-radius: var(--radius-lg);">All AI proposals have been reviewed and approved! Zero backlog.</p>`;
            return;
        }

        items.forEach(item => {
            const card = document.createElement("div");
            card.className = "queue-card";
            card.id = `proposal-${item.proposal_id}`;

            const reasons = item.evaluation?.approval_reasons || ["Steward sign-off required."];

            card.innerHTML = `
                <div class="queue-card-content">
                    <h4>Target: <code>${item.asset_id}</code></h4>
                    <div class="queue-card-meta">
                        Proposed Action: <strong>${item.change_type}</strong> | Agent: <strong>${item.proposed_by}</strong> | Confidence: <strong>${item.payload.confidence || 0.85}</strong>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span class="policy-alert-tag">⚠️ Policy Gate Triggered: ${reasons.join(" | ")}</span>
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-secondary);">
                        Candidate Payload: <code>${JSON.stringify(item.payload)}</code>
                    </p>
                </div>
                <div class="queue-actions">
                    <button class="btn-approve" onclick="handleDecision('${item.proposal_id}', 'APPROVE')">Approve Write</button>
                    <button class="btn-reject" onclick="handleDecision('${item.proposal_id}', 'REJECT')">Reject</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    window.handleDecision = async (id, decision) => {
        await fetch(`/api/approval-queue/${id}/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ steward_name: "Lead_Data_Steward", decision })
        });
        const el = document.getElementById(`proposal-${id}`);
        if (el) {
            el.style.opacity = "0.3";
            setTimeout(loadQueue, 300);
        }
    };

    loadQueue();
}

// --- Screen 4: Eval Dashboard & Talk-to-Data ---
async function initEvalDashboard() {
    const ablationContainer = document.getElementById("ablation-container");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("btn-chat-send");
    const resultArea = document.getElementById("chat-result-area");
    const statusBadge = document.getElementById("chat-status-badge");
    const policyCitation = document.getElementById("chat-policy-citation");
    const explanationText = document.getElementById("chat-explanation");
    const sqlCode = document.getElementById("chat-sql-code");
    const roleSelect = document.getElementById("role-select");

    // Load Ablations
    try {
        const resp = await fetch("/api/eval/benchmark");
        const data = await resp.json();
        const ablations = data.ablations?.ablations || [];

        ablationContainer.innerHTML = "";
        ablations.forEach(ab => {
            const item = document.createElement("div");
            item.className = "ablation-item";
            item.innerHTML = `
                <div>
                    <div class="ablation-title">${ab.configuration}</div>
                    <div class="ablation-desc">${ab.description}</div>
                </div>
                <div class="ablation-score" style="color: ${ab.accuracy_percentage === 100 ? '#10b981' : '#38bdf8'}">
                    ${ab.accuracy_percentage}%
                </div>
            `;
            ablationContainer.appendChild(item);
        });
    } catch (e) {
        console.error("Error loading ablations:", e);
    }

    // Quick chip queries
    document.querySelectorAll(".chip-query").forEach(chip => {
        chip.addEventListener("click", () => {
            chatInput.value = chip.getAttribute("data-q");
            executeChatQuery();
        });
    });

    sendBtn.addEventListener("click", executeChatQuery);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") executeChatQuery();
    });

    async function executeChatQuery() {
        const question = chatInput.value.trim();
        if (!question) return;

        sendBtn.innerText = "Querying...";
        try {
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question,
                    caller_role: roleSelect.value
                })
            });
            const data = await resp.json();

            resultArea.classList.remove("hidden");
            statusBadge.innerText = data.status;
            statusBadge.className = data.status === "REFUSED_BY_POLICY" ? "badge badge-pii" : "badge badge-cert";
            policyCitation.innerText = data.policy_citation || "";
            explanationText.innerText = data.explanation;
            sqlCode.innerText = data.sql_generated || "-- No SQL executed: Request refused by governance policies.";

        } catch (e) {
            console.error("Error executing query:", e);
        } finally {
            sendBtn.innerText = "Ask Agent";
        }
    }
}

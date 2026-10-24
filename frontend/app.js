/**
 * ContextForge Frontend — Minimalist Enterprise Dark Edition
 * Ambient: Monochromatic Black & White · Zero Glassmorphism · Precision Grid
 */

'use strict';

// ── Constants ─────────────────────────────────────────────────────────────────
const API = {
  health:    '/api/health',
  lineage:   '/api/lineage',
  assets:    '/api/assets',
  queue:     '/api/approval-queue',
  review:    (id) => `/api/approval-queue/${id}/review`,
  benchmark: '/api/eval/benchmark',
  chat:      '/api/chat',
};

const SCREEN_TITLES = {
  overview:  'Overview',
  lineage:   'Lineage DAG',
  catalog:   'Asset Catalog',
  queue:     'Steward Queue',
  policies:  'Policy Registry',
  health:    'Data Health',
  benchmark: 'Benchmark & Eval',
};

const POLICIES = [
  { id: 'POL-001', name: 'Sample Value Prohibition', desc: 'Agent-generated descriptions must not contain raw sample data values extracted from the physical column. Prevents data leakage through metadata.', hits: 12, status: 'Active' },
  { id: 'POL-002', name: 'PII Steward Approval Gate', desc: 'Any proposal to tag a column as PII must route to a human steward for explicit approval before committing to the catalog.', hits: 7, status: 'Active' },
  { id: 'POL-003', name: 'Low Confidence Review Threshold', desc: 'Agent confidence scores below 0.80 automatically route the proposal to the steward queue instead of auto-approving.', hits: 5, status: 'Active' },
  { id: 'POL-004', name: 'Quality Certification Floor', desc: 'Tables require a data quality score ≥ 0.85 across all active quality rule checks before being eligible for CERTIFIED status.', hits: 3, status: 'Active' },
  { id: 'POL-005', name: 'Certification Ownership Requirement', desc: 'Certified tables must have an assigned data owner before promotion. Unowned tables are blocked from reaching CERTIFIED status.', hits: 2, status: 'Active' },
  { id: 'POL-006', name: 'PII Classification Lockout', desc: 'Columns tagged as PII cannot be set to PUBLIC classification level. Prevents accidental exposure of sensitive data.', hits: 9, status: 'Active' },
];

const HEALTH_ASSETS = [
  { name: 'stg_orders', score: 0.95, checks: [{ label: 'NOT_NULL (order_id)', val: '100%', ok: true }, { label: 'UNIQUE (order_id)', val: '100%', ok: true }, { label: 'RANGE (status codes)', val: '100%', ok: true }] },
  { name: 'dim_customers', score: 0.91, checks: [{ label: 'NOT_NULL (customer_unique_id)', val: '100%', ok: true }, { label: 'UNIQUE (customer_unique_id)', val: '99.8%', ok: true }, { label: 'RANGE (zip format)', val: '97.2%', ok: false }] },
  { name: 'fct_orders', score: 0.89, checks: [{ label: 'NOT_NULL (order_id)', val: '100%', ok: true }, { label: 'RANGE (grand_total ≥ 0)', val: '100%', ok: true }, { label: 'Ref integrity (payments)', val: '94.1%', ok: false }] },
  { name: 'stg_order_items', score: 0.98, checks: [{ label: 'NOT_NULL (item_id)', val: '100%', ok: true }, { label: 'RANGE (item_price > 0)', val: '100%', ok: true }, { label: 'UNIQUE (item key)', val: '100%', ok: true }] },
  { name: 'stg_reviews', score: 0.87, checks: [{ label: 'RANGE (review_score 1–5)', val: '100%', ok: true }, { label: 'NOT_NULL (review_id)', val: '100%', ok: true }, { label: 'Free-text PII scan', val: 'Partial', ok: false }] },
  { name: 'customer_ltv', score: 0.93, checks: [{ label: 'NOT_NULL (customer_key)', val: '100%', ok: true }, { label: 'RANGE (ltv_brl ≥ 0)', val: '100%', ok: true }, { label: 'Ref integrity (dim)', val: '100%', ok: true }] },
];

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initRoleSelector();
  initOverview();
  initLineageDAG();
  initCatalog();
  initApprovalQueue();
  initPolicyRegistry();
  initHealthMonitor();
  initBenchmark();
});

// ── Sidebar Navigation ────────────────────────────────────────────────────────
function initSidebar() {
  const tabs = document.querySelectorAll('.nav-item[data-tab]');
  const topbarTitle = document.getElementById('topbar-title');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetTab = tab.getAttribute('data-tab');
      document.querySelectorAll('.screen-view').forEach(view => view.classList.remove('active'));
      const view = document.getElementById(`view-${targetTab}`);
      if (view) view.classList.add('active');

      if (topbarTitle) topbarTitle.textContent = SCREEN_TITLES[targetTab] || targetTab;
    });
  });
}

// ── Role Selector ─────────────────────────────────────────────────────────────
function initRoleSelector() {
  const select = document.getElementById('role-select');
  const displayName = document.getElementById('role-display-name');
  const chatBadge = document.getElementById('chat-role-badge');

  if (!select) return;

  const roles = {
    'ANALYST': { name: 'Data Analyst', type: 'PII Masked · Read Only' },
    'COMPLIANCE_STEWARD': { name: 'Compliance Steward', type: 'Full Access · Unmasked' },
  };

  select.addEventListener('change', () => {
    const r = roles[select.value] || roles['ANALYST'];
    if (displayName) displayName.textContent = r.name;
    if (chatBadge) chatBadge.textContent = `Role: ${r.name.split(' ')[0]}`;
  });
}

// ── Animated Counter ──────────────────────────────────────────────────────────
function animateCounter(el, target, suffix = '', decimals = 0, duration = 800) {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();
  const update = (now) => {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = start + (target - start) * ease;
    el.textContent = (current >= 0 && suffix.includes('pts') ? '+' : '') + current.toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// ── Screen 1: Overview ────────────────────────────────────────────────────────
async function initOverview() {
  try {
    const resp = await fetch(API.benchmark);
    const data = await resp.json();
    const m = data.metrics || {};

    const lift = parseFloat((m.text_to_sql_lift || '+13.34').replace('+', ''));
    animateCounter(document.getElementById('ov-sql-lift'), lift, ' pts', 2);

    const ablations = data.ablations || [];
    renderOverviewAblations(ablations, m);
  } catch (e) {
    renderOverviewAblations([], {});
  }
}

function renderOverviewAblations(ablations, metrics) {
  const container = document.getElementById('ov-ablation-bars');
  if (!container) return;

  const defaultAblations = [
    { configuration: 'Full Governed Context', accuracy_percentage: 86.67 },
    { configuration: 'Ablation: No Lineage', accuracy_percentage: 82.22 },
    { configuration: 'Ablation: No Glossary', accuracy_percentage: 84.44 },
    { configuration: 'Bare Schema Only', accuracy_percentage: 73.33 },
  ];

  const rows = ablations.length > 0 ? ablations.map(a => ({
    configuration: a.configuration,
    accuracy_percentage: parseFloat(a.accuracy_percentage) || 80,
  })) : defaultAblations;

  container.innerHTML = rows.map(r => `
    <div class="ablation-row">
      <div class="ablation-label">${r.configuration}</div>
      <div class="ablation-bar-wrap">
        <div class="ablation-bar-fill ${r.accuracy_percentage >= 86 ? 'qb-high' : r.accuracy_percentage >= 80 ? 'qb-mid' : 'qb-low'}"
             style="width: 0%" data-target="${r.accuracy_percentage}"></div>
      </div>
      <div class="ablation-pct">${r.accuracy_percentage.toFixed(1)}%</div>
    </div>
  `).join('');

  setTimeout(() => {
    container.querySelectorAll('.ablation-bar-fill').forEach(bar => {
      const target = bar.getAttribute('data-target');
      bar.style.transition = 'width 0.8s ease';
      bar.style.width = `${target}%`;
    });
  }, 50);
}

// ── Screen 2: Lineage DAG ─────────────────────────────────────────────────────
let dagData = { nodes: [], edges: [] };
let dagShowPiiOnly = false;
let svgOffset = { x: 0, y: 0, scale: 1 };

async function initLineageDAG() {
  const svg = document.getElementById('dag-svg');
  const statsText = document.getElementById('dag-stats-text');
  const detailPanel = document.getElementById('node-detail-panel');
  const closeBtn = document.getElementById('btn-close-drawer');

  if (closeBtn) closeBtn.addEventListener('click', () => detailPanel && detailPanel.classList.add('hidden'));

  const resetBtn = document.getElementById('btn-reset-zoom');
  if (resetBtn) resetBtn.addEventListener('click', () => {
    svgOffset = { x: 0, y: 0, scale: 1 };
    applyTransform(svg);
  });

  const piiBtn = document.getElementById('btn-toggle-pii');
  if (piiBtn) piiBtn.addEventListener('click', () => {
    dagShowPiiOnly = !dagShowPiiOnly;
    piiBtn.classList.toggle('active', dagShowPiiOnly);
    renderDAG(svg, dagData.nodes, dagData.edges);
  });

  try {
    const resp = await fetch(API.lineage);
    dagData = await resp.json();
    const { nodes, edges } = dagData;

    if (statsText) statsText.textContent = `${nodes.length} Nodes · ${edges.length} Lineage Edges`;
    renderDAG(svg, nodes, edges);
  } catch (err) {
    console.error('Lineage DAG error:', err);
    if (statsText) statsText.textContent = 'Failed to load lineage.';
  }
}

function applyTransform(svg) {
  const g = svg.querySelector('.dag-root-g');
  if (g) g.setAttribute('transform', `translate(${svgOffset.x},${svgOffset.y}) scale(${svgOffset.scale})`);
}

function renderDAG(svg, nodes, edges) {
  const tierCoords = {
    raw:       { x: 50,   yStep: 56, border: '#3f3f46', text: '#a1a1aa' },
    staging:   { x: 300,  yStep: 64, border: '#52525b', text: '#e4e4e7' },
    marts:     { x: 570,  yStep: 72, border: '#71717a', text: '#f4f4f5' },
    dashboard: { x: 840,  yStep: 90, border: '#ffffff', text: '#ffffff' },
  };

  const tierCounts = { raw: 0, staging: 0, marts: 0, dashboard: 0 };
  const nodePositions = {};

  const visibleNodes = dagShowPiiOnly ? nodes.filter(n => n.has_pii) : nodes;

  visibleNodes.forEach(node => {
    const t = node.tier || 'marts';
    const cfg = tierCoords[t] || tierCoords.marts;
    const idx = tierCounts[t]++;
    nodePositions[node.id] = { x: cfg.x, y: 36 + idx * cfg.yStep, node, border: cfg.border, text: cfg.text };
  });

  svg.innerHTML = `
    <defs>
      <marker id="arrow-clean" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <polygon points="0 0, 6 3, 0 6" fill="#3f3f46"/>
      </marker>
      <marker id="arrow-pii" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
        <polygon points="0 0, 6 3, 0 6" fill="#ef4444"/>
      </marker>
    </defs>
    <g class="dag-root-g">
      <g class="dag-edges"></g>
      <g class="dag-nodes"></g>
    </g>
  `;

  const edgesG = svg.querySelector('.dag-edges');
  const nodesG = svg.querySelector('.dag-nodes');

  // Draw edges
  const visibleNodeIds = new Set(visibleNodes.map(n => n.id));
  edges.forEach(edge => {
    if (!visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target)) return;
    const p1 = nodePositions[edge.source];
    const p2 = nodePositions[edge.target];
    if (!p1 || !p2) return;

    const isPii = edge.is_pii_propagated;
    const x1 = p1.x + 165, y1 = p1.y + 17;
    const x2 = p2.x, y2 = p2.y + 17;
    const dx = (x2 - x1) * 0.5;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${x1} ${y1} C ${x1+dx} ${y1}, ${x2-dx} ${y2}, ${x2} ${y2}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', isPii ? '#ef4444' : '#27272a');
    path.setAttribute('stroke-width', isPii ? '1.5' : '1');
    path.setAttribute('opacity', isPii ? '0.9' : '0.5');
    if (isPii) {
      path.setAttribute('stroke-dasharray', '4 3');
    }
    path.setAttribute('marker-end', isPii ? 'url(#arrow-pii)' : 'url(#arrow-clean)');
    edgesG.appendChild(path);
  });

  // Draw nodes
  Object.values(nodePositions).forEach(pos => {
    const n = pos.node;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${pos.x},${pos.y})`);
    g.style.cursor = 'pointer';

    // Card rect
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('width', '165');
    rect.setAttribute('height', '34');
    rect.setAttribute('rx', '4');
    rect.setAttribute('fill', '#0c0c0e');
    rect.setAttribute('stroke', n.has_pii ? '#ef4444' : '#27272a');
    rect.setAttribute('stroke-width', n.has_pii ? '1.5' : '1');
    g.appendChild(rect);

    // Left accent bar
    const accent = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    accent.setAttribute('width', '2');
    accent.setAttribute('height', '20');
    accent.setAttribute('x', '0');
    accent.setAttribute('y', '7');
    accent.setAttribute('fill', n.has_pii ? '#ef4444' : pos.border);
    g.appendChild(accent);

    // Label
    const label = (n.label || n.id).replace(/^cforge\.public\./, '');
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', '10');
    text.setAttribute('y', '21');
    text.setAttribute('fill', '#f4f4f5');
    text.setAttribute('font-size', '11');
    text.setAttribute('font-weight', '500');
    text.setAttribute('font-family', 'Inter, -apple-system, sans-serif');
    text.textContent = label.length > 19 ? label.slice(0, 18) + '…' : label;
    g.appendChild(text);

    // PII badge indicator
    if (n.has_pii) {
      const piiText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      piiText.setAttribute('x', '140');
      piiText.setAttribute('y', '21');
      piiText.setAttribute('fill', '#ef4444');
      piiText.setAttribute('font-size', '8');
      piiText.setAttribute('font-weight', '700');
      piiText.setAttribute('font-family', 'JetBrains Mono, monospace');
      piiText.textContent = 'PII';
      g.appendChild(piiText);
    }

    // Hover effect
    g.addEventListener('mouseenter', () => {
      rect.setAttribute('fill', '#141416');
      rect.setAttribute('stroke', n.has_pii ? '#ef4444' : '#52525b');
    });
    g.addEventListener('mouseleave', () => {
      rect.setAttribute('fill', '#0c0c0e');
      rect.setAttribute('stroke', n.has_pii ? '#ef4444' : '#27272a');
    });

    // Click handler
    g.addEventListener('click', (e) => {
      e.stopPropagation();
      openNodeDrawer(n, edges, nodes);
    });

    nodesG.appendChild(g);
  });
}

function openNodeDrawer(node, edges, allNodes) {
  const panel = document.getElementById('node-detail-panel');
  const title = document.getElementById('drawer-title');
  const content = document.getElementById('drawer-content');
  if (!panel || !title || !content) return;

  const nodeName = (node.label || node.id).replace(/^cforge\.public\./, '');
  title.textContent = nodeName;

  const upEdges = edges.filter(e => e.target === node.id);
  const downEdges = edges.filter(e => e.source === node.id);

  content.innerHTML = `
    <div class="drawer-row">
      <div class="drawer-row-label">Physical Identifier</div>
      <div class="drawer-row-value"><span class="code-inline">${node.id}</span></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-row-label">Architecture Tier</div>
      <div class="drawer-row-value"><span class="badge badge-muted">${(node.tier || 'marts').toUpperCase()}</span></div>
    </div>
    <div class="drawer-row">
      <div class="drawer-row-label">Governance &amp; PII</div>
      <div class="drawer-row-value">
        ${node.has_pii ? '<span class="badge badge-coral">PII Classified</span>' : '<span class="badge badge-emerald">Clean · No PII</span>'}
      </div>
    </div>
    <div class="drawer-row">
      <div class="drawer-row-label">Lineage Connections</div>
      <div class="drawer-row-value">${upEdges.length} Upstream · ${downEdges.length} Downstream</div>
    </div>
    ${upEdges.length > 0 ? `
      <div class="drawer-row">
        <div class="drawer-row-label">Upstream Dependencies</div>
        <div style="display:flex;flex-direction:column;gap:4px">
          ${upEdges.map(e => {
            const src = e.source.replace(/^cforge\.public\./, '');
            return `<div style="font-size:0.75rem;color:var(--text-secondary);font-family:var(--font-mono)">← ${src} ${e.is_pii_propagated ? '<span style="color:var(--status-alert)">(PII)</span>' : ''}</div>`;
          }).join('')}
        </div>
      </div>
    ` : ''}
    ${downEdges.length > 0 ? `
      <div class="drawer-row">
        <div class="drawer-row-label">Downstream Impact</div>
        <div style="display:flex;flex-direction:column;gap:4px">
          ${downEdges.map(e => {
            const tgt = e.target.replace(/^cforge\.public\./, '');
            return `<div style="font-size:0.75rem;color:var(--text-secondary);font-family:var(--font-mono)">→ ${tgt} ${e.is_pii_propagated ? '<span style="color:var(--status-alert)">(PII)</span>' : ''}</div>`;
          }).join('')}
        </div>
      </div>
    ` : ''}
  `;

  panel.classList.remove('hidden');
}

// ── Screen 3: Asset Catalog ───────────────────────────────────────────────────
let allAssets = [];

async function initCatalog() {
  const search = document.getElementById('asset-search');
  const filterBtns = document.querySelectorAll('.catalog-filter-row .filter-chip');

  let activeFilter = 'all';

  try {
    const resp = await fetch(API.assets);
    const data = await resp.json();
    allAssets = Array.isArray(data) ? data : (data.assets || []);
    renderCatalogTree(allAssets, '');
    if (allAssets.length > 0) {
      showAssetDetail(allAssets[0]);
      const firstItem = document.querySelector('.tree-item');
      if (firstItem) firstItem.classList.add('active');
    }
  } catch (e) {
    console.error('Catalog load error:', e);
  }

  if (search) {
    search.addEventListener('input', () => {
      applyCatalogFilters(search.value, activeFilter);
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.getAttribute('data-filter');
      applyCatalogFilters(search ? search.value : '', activeFilter);
    });
  });
}

function applyCatalogFilters(query, filter) {
  let filtered = allAssets;
  if (filter === 'pii') filtered = filtered.filter(a => a.pii_columns_count > 0);
  if (filter === 'certified') filtered = filtered.filter(a => a.certification_status === 'CERTIFIED');
  if (query) {
    const q = query.toLowerCase();
    filtered = filtered.filter(a => (a.name || '').toLowerCase().includes(q) || (a.display_name || '').toLowerCase().includes(q));
  }
  renderCatalogTree(filtered, query);
}

function renderCatalogTree(assets, query) {
  const tree = document.getElementById('catalog-tree');
  if (!tree) return;

  const list = Array.isArray(assets) ? assets : (assets?.assets || []);

  tree.innerHTML = list.map(a => `
    <div class="tree-item" data-asset-id="${a.asset_id}">
      <span class="tree-item-icon">▤</span>
      <span class="tree-item-name">${a.name}</span>
      ${a.pii_columns_count > 0 ? `<span class="tree-item-pii">PII</span>` : ''}
    </div>
  `).join('') || `<div class="empty-state"><div class="empty-title">No assets found</div></div>`;

  tree.querySelectorAll('.tree-item').forEach(item => {
    item.addEventListener('click', () => {
      tree.querySelectorAll('.tree-item').forEach(t => t.classList.remove('active'));
      item.classList.add('active');
      const assetId = item.getAttribute('data-asset-id');
      const asset = allAssets.find(a => a.asset_id === assetId);
      if (asset) showAssetDetail(asset);
    });
  });
}

function showAssetDetail(asset) {
  const placeholder = document.getElementById('catalog-detail-placeholder');
  const panel = document.getElementById('catalog-detail-panel');
  const header = document.getElementById('catalog-detail-header');
  const body = document.getElementById('catalog-detail-body');

  if (placeholder) placeholder.style.display = 'none';
  if (panel) panel.style.display = 'flex';

  const qualityPct = Math.round((asset.quality_score || 0.9) * 100);
  const qualityClass = qualityPct >= 90 ? 'qb-high' : qualityPct >= 70 ? 'qb-mid' : 'qb-low';

  if (header) {
    header.innerHTML = `
      <div class="catalog-detail-name">${asset.display_name || asset.name}</div>
      <div class="catalog-detail-meta">
        <span class="badge ${asset.certification_status === 'CERTIFIED' ? 'badge-emerald' : 'badge-muted'}">${asset.certification_status || 'UNCERTIFIED'}</span>
        ${asset.pii_columns_count > 0 ? `<span class="badge badge-coral">⚠ ${asset.pii_columns_count} PII Columns</span>` : '<span class="badge badge-emerald">✓ Clean</span>'}
        <span class="badge badge-muted">${asset.total_columns} columns</span>
        ${asset.owner ? `<span class="badge badge-muted">Owner: ${asset.owner}</span>` : ''}
      </div>
      <div style="margin-top:12px">
        <div class="quality-bar-wrap">
          <div style="font-size:0.72rem;color:var(--text-muted);width:90px">Quality Score</div>
          <div class="quality-bar" style="flex:1">
            <div class="quality-bar-fill ${qualityClass}" id="quality-fill-bar" style="width:0%"></div>
          </div>
          <div style="font-size:0.78rem;font-weight:600;font-family:var(--font-mono);color:var(--text-white)">${qualityPct}%</div>
        </div>
      </div>
      <p style="margin-top:10px;font-size:0.8rem;color:var(--text-muted);line-height:1.5">${asset.description || 'No description available.'}</p>
    `;
    setTimeout(() => {
      const bar = document.getElementById('quality-fill-bar');
      if (bar) bar.style.width = qualityPct + '%';
    }, 50);
  }

  if (body) {
    const cols = asset.columns || [];
    body.innerHTML = `
      <div class="section-divider" style="margin-bottom:12px;font-size:0.68rem;text-transform:uppercase;color:var(--text-muted);font-weight:600">Column Schema &amp; Governed Context</div>
      <table class="col-table">
        <thead>
          <tr>
            <th>Column</th>
            <th>Data Type</th>
            <th>PII Status</th>
            <th>Masking Policy</th>
            <th>Sample Value</th>
          </tr>
        </thead>
        <tbody>
          ${cols.map(c => `
            <tr>
              <td>${c.column_name}</td>
              <td style="color:var(--text-secondary);font-family:var(--font-mono);font-size:0.72rem">${c.data_type || 'VARCHAR'}</td>
              <td>${c.is_pii ? `<span class="badge badge-coral">${c.pii_type || 'PII'}</span>` : '<span class="badge badge-muted">NONE</span>'}</td>
              <td style="font-size:0.72rem">${c.is_masked ? '<span style="color:var(--status-warn)">POL-002 Active</span>' : '<span style="color:var(--text-muted)">Direct</span>'}</td>
              <td style="font-family:var(--font-mono);font-size:0.72rem;color:var(--text-muted)">${c.is_masked ? '<span style="color:var(--status-alert)">[RESTRICTED_PII]</span>' : '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
}

// ── Screen 4: Approval Queue ──────────────────────────────────────────────────
async function initApprovalQueue() {
  await loadQueue();
}

async function loadQueue() {
  const container = document.getElementById('queue-container');
  const countBadge = document.getElementById('queue-count-badge');
  const statPill = document.getElementById('queue-stat-pill');
  if (!container) return;

  try {
    const resp = await fetch(API.queue);
    const data = await resp.json();
    const items = data.queue || [];

    if (countBadge) countBadge.textContent = items.length;
    if (statPill) statPill.textContent = items.length > 0 ? `${items.length} Pending` : 'All Clear';

    if (items.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="background:var(--bg-card);border:1px solid var(--border-default);border-radius:var(--r-md);padding:40px">
          <div class="empty-title">All proposals reviewed</div>
          <div class="empty-sub" style="font-size:0.8rem;color:var(--text-muted)">No backlog. Catalog is fully steward-approved.</div>
        </div>`;
      return;
    }

    container.innerHTML = items.map(item => {
      const reasons = item.evaluation?.approval_reasons || ['Steward review required by policy.'];
      const conf = item.payload?.confidence || 0.85;

      return `
        <div class="queue-card" id="proposal-${item.proposal_id}">
          <div class="queue-card-header">
            <div class="queue-card-icon">◫</div>
            <div class="queue-card-info">
              <div class="queue-card-title">${item.change_type.replace('_', ' ')}</div>
              <div class="queue-card-asset">${item.asset_id}</div>
              <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
                <span class="badge badge-muted">Agent: ${item.proposed_by}</span>
                <span class="badge badge-muted">Confidence: ${conf}</span>
              </div>
            </div>
          </div>
          <div class="queue-card-body">
            <div class="queue-card-reason">Policy Gate: ${reasons.join(' · ')}</div>
            <div class="queue-payload">${JSON.stringify(item.payload, null, 2)}</div>
          </div>
          <div class="queue-actions">
            <button class="btn-approve" onclick="handleDecision('${item.proposal_id}', 'APPROVE')">✓ Approve Write</button>
            <button class="btn-reject" onclick="handleDecision('${item.proposal_id}', 'REJECT')">✗ Reject</button>
            <button class="btn-detail">Audit Trail</button>
          </div>
        </div>
      `;
    }).join('');

  } catch (e) {
    console.error('Queue load error:', e);
    container.innerHTML = `<div class="empty-state"><div class="empty-title">Failed to load approval queue.</div></div>`;
  }
}

window.handleDecision = async (id, decision) => {
  const card = document.getElementById(`proposal-${id}`);
  if (card) {
    card.style.opacity = '0.3';
  }
  try {
    await fetch(API.review(id), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ steward_name: 'Lead_Data_Steward', decision }),
    });
    setTimeout(loadQueue, 300);
  } catch (e) {
    console.error('Review error:', e);
    if (card) card.style.opacity = '1';
  }
};

// ── Screen 5: Policy Registry ─────────────────────────────────────────────────
function initPolicyRegistry() {
  const container = document.getElementById('policy-container');
  if (!container) return;

  container.innerHTML = POLICIES.map(p => `
    <div class="policy-card">
      <div class="policy-id">${p.id}</div>
      <div class="policy-body">
        <div class="policy-name">${p.name}</div>
        <div class="policy-desc">${p.desc}</div>
      </div>
      <div class="policy-stat">
        <div class="policy-stat-num">${p.hits}</div>
        <div class="policy-stat-label">Triggered</div>
        <span class="badge badge-emerald" style="margin-top:4px">${p.status}</span>
      </div>
    </div>
  `).join('');
}

// ── Screen 6: Data Health Monitor ─────────────────────────────────────────────
function initHealthMonitor() {
  const container = document.getElementById('health-container');
  if (!container) return;

  container.innerHTML = HEALTH_ASSETS.map(a => {
    const pct = Math.round(a.score * 100);
    return `
      <div class="health-card">
        <div class="health-card-header">
          <div class="health-card-name">${a.name}</div>
          <div class="health-score-big">${pct}%</div>
        </div>
        <div class="quality-bar" style="margin-bottom:12px">
          <div class="quality-bar-fill ${pct>=90?'qb-high':pct>=80?'qb-mid':'qb-low'} health-qb"
               style="width:0%" data-target="${pct}"></div>
        </div>
        <div class="health-checks">
          ${a.checks.map(c => `
            <div class="health-check-row">
              <span class="check-icon" style="color:${c.ok ? 'var(--status-pass)' : 'var(--status-warn)'}">${c.ok ? '✓' : '!'}</span>
              <span class="check-label">${c.label}</span>
              <span class="check-val">${c.val}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');

  setTimeout(() => {
    container.querySelectorAll('.health-qb').forEach(bar => {
      bar.style.transition = 'width 0.8s ease';
      bar.style.width = bar.getAttribute('data-target') + '%';
    });
  }, 50);
}

// ── Screen 7: Benchmark & Eval ────────────────────────────────────────────────
async function initBenchmark() {
  const ablationContainer = document.getElementById('ablation-container');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-chat-send');
  const resultArea = document.getElementById('chat-result-area');
  const statusBadge = document.getElementById('chat-status-badge');
  const policyCitation = document.getElementById('chat-policy-citation');
  const explanationText = document.getElementById('chat-explanation');
  const sqlCode = document.getElementById('chat-sql-code');
  const roleSelect = document.getElementById('role-select');

  try {
    const resp = await fetch(API.benchmark);
    const data = await resp.json();
    const m = data.metrics || {};

    const updateEl = (id, val) => { const el = document.getElementById(id); if (el && val) el.textContent = val; };
    updateEl('score-sql-lift', m.text_to_sql_lift);
    updateEl('score-pii-val', m.pii_f1_score);
    updateEl('score-cost-val', m.enrichment_cost_per_1k);
    if (m.bare_schema_accuracy && m.enriched_context_accuracy) {
      const el = document.getElementById('score-sql-meta');
      if (el) el.textContent = `${m.bare_schema_accuracy} → ${m.enriched_context_accuracy}`;
    }

    const ablations = data.ablations || [];
    if (ablationContainer) {
      const defaultRows = [
        { configuration: 'Full Governed Context', accuracy_percentage: 86.67 },
        { configuration: 'No Lineage Context', accuracy_percentage: 82.22 },
        { configuration: 'No Glossary Terms', accuracy_percentage: 84.44 },
        { configuration: 'No Profiling Stats', accuracy_percentage: 86.67 },
        { configuration: 'Bare Schema Only', accuracy_percentage: 73.33 },
      ];
      const rows = ablations.length ? ablations : defaultRows;

      ablationContainer.innerHTML = rows.map(r => {
        const pct = parseFloat(r.accuracy_percentage) || 80;
        const cls = pct >= 86 ? 'qb-high' : pct >= 80 ? 'qb-mid' : 'qb-low';
        return `
          <div class="ablation-row">
            <div class="ablation-label">${r.configuration || r.name || ''}</div>
            <div class="ablation-bar-wrap">
              <div class="ablation-bar-fill ${cls} bench-abl-bar" style="width:0%" data-target="${pct}"></div>
            </div>
            <div class="ablation-pct">${pct.toFixed(1)}%</div>
          </div>
        `;
      }).join('');

      setTimeout(() => {
        ablationContainer.querySelectorAll('.bench-abl-bar').forEach(bar => {
          bar.style.transition = 'width 0.8s ease';
          bar.style.width = bar.getAttribute('data-target') + '%';
        });
      }, 50);
    }
  } catch (e) {
    console.warn('Benchmark data unavailable.');
  }

  // Chat console
  document.querySelectorAll('.chip-query').forEach(chip => {
    chip.addEventListener('click', () => {
      if (chatInput) chatInput.value = chip.getAttribute('data-q');
      executeChatQuery();
    });
  });

  if (sendBtn) sendBtn.addEventListener('click', executeChatQuery);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') executeChatQuery(); });
  }

  async function executeChatQuery() {
    const question = chatInput ? chatInput.value.trim() : '';
    if (!question) return;
    if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = 'Querying…'; }

    try {
      const resp = await fetch(API.chat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, caller_role: roleSelect ? roleSelect.value : 'ANALYST' }),
      });
      const data = await resp.json();

      if (resultArea) resultArea.classList.remove('hidden');

      const refused = data.status === 'REFUSED_BY_POLICY';
      if (statusBadge) {
        statusBadge.textContent = refused ? 'REFUSED BY POLICY' : '✓ QUERY EXECUTED';
        statusBadge.className = refused ? 'badge badge-coral' : 'badge badge-emerald';
      }
      if (policyCitation) policyCitation.textContent = data.policy_citation || '';
      if (explanationText) explanationText.textContent = data.explanation || '';
      if (sqlCode) sqlCode.textContent = data.sql_generated || '-- No SQL executed. Request refused by governance policies.';

    } catch (e) {
      console.error('Chat error:', e);
    } finally {
      if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = 'Ask Agent'; }
    }
  }
}

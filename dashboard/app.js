const sampleRows = [
  {
    "콘텐츠명(주제)": "샘플",
    "하위_키워드": "샘플 결말 해석",
    "추천요약": "공략 우선",
    "분석기준수요(월간)": 120000,
    "키워드검색수요(월간_직접)": 80000,
    "총문서량(네이버)": 250,
    "네이버_포화율(%)": 0.21,
    "추천도(네이버)": "★★★",
    "총영상수(유튜브)": 140,
    "추천도(유튜브)": "★★",
    "기회점수(0-100)": 88,
    "신뢰도(0-100)": 80,
    "황금키워드": "Y",
    "판정근거": "네이버 직접수요 대비 문서량 낮음",
    "키워드수요_상태": "측정완료",
    "네이버_상태": "측정완료",
    "다음_상태": "측정완료",
    "유튜브_상태": "측정완료",
  },
];

const state = {
  rows: [],
  payload: null,
  apiAvailable: false,
  verdictFilter: "all",
  topicFilter: "all",
  search: "",
};

const formatNumber = new Intl.NumberFormat("ko-KR");
const number = (value) => {
  const n = Number(String(value ?? "0").replace(/,/g, ""));
  return Number.isFinite(n) ? n : 0;
};

const text = (value) => String(value ?? "");
const escapeHtml = (value) => text(value)
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

const isGolden = (row) => row["황금키워드"] === "Y" || row.is_golden === true;
const getTopic = (row) => row["콘텐츠명(주제)"] || row.topic || row.title || "";
const getKeyword = (row) => row["하위_키워드"] || row.keyword || "";
const getVerdict = (row) => row["추천요약"] || (isGolden(row) ? "공략 우선" : "검토");
const getDemand = (row) => number(row["분석기준수요(월간)"] || row["통합검색수요(전체)"] || row.total_demand);
const getDirectDemand = (row) => number(row["키워드검색수요(월간_직접)"] || row.keyword_demand);
const getDocs = (row) => number(row["총문서량(네이버)"] || row.naver_docs);
const getScore = (row) => number(row["기회점수(0-100)"] || row["기회점수"] || row.score);
const getConfidence = (row) => number(row["신뢰도(0-100)"] || row["신뢰도"] || row.confidence);
const getNaverSaturation = (row) => row["네이버_포화율(%)"] ?? row["네이버_포화율"] ?? "";

function parseCsv(textValue) {
  const clean = textValue.replace(/^\uFEFF/, "");
  const lines = clean.split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function splitCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];
    if (char === "\"" && quoted && next === "\"") {
      current += "\"";
      i += 1;
    } else if (char === "\"") {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function loadLatest() {
  try {
    const payload = await fetchJson("/api/latest", { cache: "no-store" });
    state.apiAvailable = true;
    setApiBadge(true);
    applyPayload(payload);
  } catch (apiError) {
    try {
      const payload = await fetchJson("../results/latest_portfolio.json", { cache: "no-store" });
      state.apiAvailable = false;
      setApiBadge(false);
      applyPayload(payload);
    } catch (staticError) {
      state.apiAvailable = false;
      setApiBadge(false);
      applyPayload({ mode: "sample", rows: sampleRows });
    }
  }
}

function applyPayload(payload) {
  state.payload = payload;
  state.rows = payload.rows || payload || [];
  state.topicFilter = "all";
  render();
}

function setApiBadge(isAvailable) {
  const badge = document.querySelector("#apiBadge");
  badge.textContent = isAvailable ? "분석 가능" : "로컬 데이터";
  badge.className = `badge ${isAvailable ? "ok" : "warn"}`;
}

function setRunState(label, type = "") {
  const badge = document.querySelector("#runState");
  badge.textContent = label;
  badge.className = `badge ${type}`;
}

async function loadTrends() {
  const category = document.querySelector("#categorySelect").value;
  const list = document.querySelector("#trendList");
  list.innerHTML = `<div class="empty-state">탐색 중</div>`;
  if (!state.apiAvailable) {
    list.innerHTML = `<div class="empty-state">대시보드 서버 필요</div>`;
    showCommand(`python3 dashboard/server.py --port 8766`);
    return;
  }

  try {
    const payload = await fetchJson(`/api/trends?category=${encodeURIComponent(category)}&top=8`, { cache: "no-store" });
    renderTrends(payload.items || []);
  } catch (error) {
    list.innerHTML = `<div class="empty-state">트렌드 탐색 실패</div>`;
  }
}

function renderTrends(items) {
  const list = document.querySelector("#trendList");
  if (!items.length) {
    list.innerHTML = `<div class="empty-state">후보 없음</div>`;
    return;
  }
  list.innerHTML = items.map((item) => `
    <button class="trend-card" type="button" data-title="${escapeHtml(item.title)}">
      <strong>${escapeHtml(item.title)}</strong>
      <span>${escapeHtml(item.source || "trend")} · ${Math.round(number(item.score))}</span>
    </button>
  `).join("");
  list.querySelectorAll(".trend-card").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelector("#titleInput").value = button.dataset.title;
      runAnalysis();
    });
  });
}

async function runAnalysis() {
  const input = document.querySelector("#titleInput");
  const rawTitles = input.value.split(",").map((item) => item.trim()).filter(Boolean);
  if (!rawTitles.length) {
    setRunState("제목 필요", "warn");
    input.focus();
    return;
  }

  if (!state.apiAvailable) {
    setRunState("서버 필요", "warn");
    showCommand(`python3 dashboard/server.py --port 8766\npython3 -m autoauthor --titles "${rawTitles.join(", ")}" --category drama`);
    return;
  }

  setRunState("분석 중", "warn");
  document.querySelector("#runAnalysis").disabled = true;
  hideCommand();
  try {
    const payload = await fetchJson("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        titles: rawTitles,
        category: document.querySelector("#categorySelect").value || "drama",
      }),
    });
    applyPayload(payload);
    setRunState("완료", "ok");
  } catch (error) {
    setRunState("실패", "warn");
    showCommand(`python3 -m autoauthor --titles "${rawTitles.join(", ")}" --category drama`);
  } finally {
    document.querySelector("#runAnalysis").disabled = false;
  }
}

function showCommand(command) {
  const box = document.querySelector("#commandBox");
  box.hidden = false;
  box.textContent = command;
}

function hideCommand() {
  const box = document.querySelector("#commandBox");
  box.hidden = true;
  box.textContent = "";
}

function handleUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const content = String(reader.result || "");
    const payload = file.name.endsWith(".json")
      ? JSON.parse(content)
      : { mode: "uploaded_csv", rows: parseCsv(content) };
    applyPayload(payload);
  };
  reader.readAsText(file, "utf-8");
}

function rowBucket(row) {
  const verdict = getVerdict(row);
  if (isGolden(row) || verdict.includes("공략")) return "gold";
  if (verdict.includes("후보")) return "candidate";
  if (verdict.includes("보류")) return "hold";
  if (verdict.includes("제외")) return "exclude";
  return "candidate";
}

function filteredRows() {
  const query = state.search.trim().toLowerCase();
  return state.rows.filter((row) => {
    if (state.topicFilter !== "all" && getTopic(row) !== state.topicFilter) return false;
    if (state.verdictFilter !== "all" && rowBucket(row) !== state.verdictFilter) return false;
    if (!query) return true;
    return `${getTopic(row)} ${getKeyword(row)} ${getVerdict(row)}`.toLowerCase().includes(query);
  });
}

function render() {
  const total = state.rows.length;
  const golden = state.rows.filter(isGolden).length;
  const direct = state.rows.filter((row) => String(row["키워드수요_상태"] || row.keyword_demand_status || "").includes("측정")).length;
  const bestScore = total ? Math.max(...state.rows.map(getScore)) : 0;

  document.querySelector("#metricTotal").textContent = formatNumber.format(total);
  document.querySelector("#metricGolden").textContent = formatNumber.format(golden);
  document.querySelector("#metricDirect").textContent = formatNumber.format(direct);
  document.querySelector("#metricScore").textContent = `${bestScore}`;
  document.querySelector("#focusCount").textContent = `${golden}`;

  renderTopicFilter();
  renderFunnel(total, golden, direct);
  renderMatrix();
  renderActions();
  renderTable();
  renderStatus();
}

function renderTopicFilter() {
  const select = document.querySelector("#topicFilter");
  const topics = [...new Set(state.rows.map(getTopic).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ko"));
  const current = state.topicFilter;
  select.innerHTML = `<option value="all">전체 주제</option>${topics.map((topic) => (
    `<option value="${escapeHtml(topic)}">${escapeHtml(topic)}</option>`
  )).join("")}`;
  select.value = topics.includes(current) ? current : "all";
  state.topicFilter = select.value;
}

function renderFunnel(total, golden, direct) {
  const measured = state.rows.filter((row) => String(row["네이버_상태"] || row.naver_status || "").includes("측정")).length;
  const steps = [
    ["후보 수집", total],
    ["공급 측정", measured],
    ["직접수요 확인", direct],
    ["황금 확정", golden],
  ];
  const max = Math.max(1, total);
  document.querySelector("#funnel").innerHTML = steps.map(([label, value], index) => `
    <div class="funnel-step">
      <div class="funnel-label">${label}</div>
      <div class="funnel-bar">
        <div class="funnel-fill" style="width:${Math.max(3, (value / max) * 100)}%; background:${["#2867c7", "#14a66a", "#5865a8", "#c98912"][index]}"></div>
      </div>
      <div class="funnel-value">${formatNumber.format(value)}</div>
    </div>
  `).join("");
}

function renderMatrix() {
  const svg = document.querySelector("#matrix");
  const maxDemand = Math.max(1, ...state.rows.map(getDemand));
  const maxDocs = Math.max(1, ...state.rows.map(getDocs));
  const plot = state.rows.slice(0, 100).map((row) => {
    const x = 72 + (Math.log10(getDemand(row) + 1) / Math.log10(maxDemand + 1)) * 500;
    const y = 298 - (Math.log10(getDocs(row) + 1) / Math.log10(maxDocs + 1)) * 230;
    const bucket = rowBucket(row);
    const fill = bucket === "gold" ? "#c98912" : bucket === "candidate" ? "#2867c7" : bucket === "hold" ? "#8a6f23" : "#8b97a7";
    const label = escapeHtml(getKeyword(row));
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${isGolden(row) ? 7 : 5}" fill="${fill}" opacity="0.86"><title>${label}</title></circle>`;
  }).join("");
  svg.innerHTML = `
    <line x1="70" y1="300" x2="590" y2="300" stroke="#cbd2dc"/>
    <line x1="70" y1="60" x2="70" y2="300" stroke="#cbd2dc"/>
    <text x="590" y="330" text-anchor="end" fill="#657181" font-size="13">검색 수요 높음</text>
    <text x="22" y="64" fill="#657181" font-size="13" transform="rotate(-90 22,64)">공급 많음</text>
    <rect x="370" y="210" width="210" height="80" rx="8" fill="#fff3d7" stroke="#f2d28f"/>
    <text x="475" y="252" text-anchor="middle" fill="#8a5a00" font-size="14" font-weight="700">기회 영역</text>
    ${plot}
  `;
}

function renderActions() {
  const box = document.querySelector("#actionList");
  const golden = [...state.rows].filter(isGolden).sort((a, b) => getScore(b) - getScore(a)).slice(0, 4);
  const fallback = [...state.rows]
    .filter((row) => rowBucket(row) === "candidate")
    .sort((a, b) => getScore(b) - getScore(a))
    .slice(0, 3);
  const rows = golden.length ? golden : fallback;
  if (!rows.length) {
    box.innerHTML = `<div class="empty-state">공략 후보 없음</div>`;
    return;
  }
  box.innerHTML = rows.map((row) => `
    <div class="action-item">
      <strong>${escapeHtml(getKeyword(row))}</strong>
      <span>${escapeHtml(getTopic(row))} · ${formatNumber.format(getDirectDemand(row) || getDemand(row))}</span>
    </div>
  `).join("");
}

function renderTable() {
  const ranked = filteredRows()
    .sort((a, b) => Number(isGolden(b)) - Number(isGolden(a)) || getScore(b) - getScore(a) || getConfidence(b) - getConfidence(a))
    .slice(0, 40);
  document.querySelector("#keywordRows").innerHTML = ranked.map((row) => {
    const saturation = getNaverSaturation(row);
    const directDemand = getDirectDemand(row);
    return `
      <tr>
        <td><strong>${escapeHtml(getKeyword(row))}</strong><br><span>${escapeHtml(getTopic(row))}</span></td>
        <td><span class="badge ${isGolden(row) ? "gold" : rowBucket(row)}">${escapeHtml(getVerdict(row))}</span></td>
        <td>${directDemand ? formatNumber.format(directDemand) : "-"}</td>
        <td>${saturation === "" || saturation == null ? "-" : `${saturation}%`}</td>
        <td>${getScore(row)} / ${getConfidence(row)}</td>
        <td>${escapeHtml(row["판정근거"] || "")}</td>
      </tr>
    `;
  }).join("");
}

function renderStatus() {
  const keys = ["키워드수요_상태", "수요상태", "네이버_상태", "다음_상태", "유튜브_상태"];
  const items = keys.map((key) => {
    const counts = state.rows.reduce((acc, row) => {
      const value = row[key] || "미기록";
      acc[value] = (acc[value] || 0) + 1;
      return acc;
    }, {});
    const detail = Object.entries(counts).map(([name, count]) => `${name} ${count}`).join(" · ");
    const ok = Object.keys(counts).some((name) => name.includes("측정완료"));
    return `
      <div class="status-item">
        <div><strong>${key}</strong><br><span>${escapeHtml(detail)}</span></div>
        <span class="badge ${ok ? "ok" : "warn"}">${ok ? "OK" : "CHECK"}</span>
      </div>
    `;
  }).join("");
  document.querySelector("#statusList").innerHTML = items;
}

function downloadCsv() {
  const rows = filteredRows();
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => {
      const value = text(row[header]).replace(/"/g, "\"\"");
      return /[",\n]/.test(value) ? `"${value}"` : value;
    }).join(",")),
  ].join("\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `autoauthor_keywords_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

document.querySelector("#loadLatest").addEventListener("click", loadLatest);
document.querySelector("#downloadCsv").addEventListener("click", downloadCsv);
document.querySelector("#fileInput").addEventListener("change", handleUpload);
document.querySelector("#findTrends").addEventListener("click", loadTrends);
document.querySelector("#runAnalysis").addEventListener("click", runAnalysis);
document.querySelector("#titleInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") runAnalysis();
});
document.querySelector("#verdictFilter").addEventListener("change", (event) => {
  state.verdictFilter = event.target.value;
  renderTable();
});
document.querySelector("#topicFilter").addEventListener("change", (event) => {
  state.topicFilter = event.target.value;
  renderTable();
});
document.querySelector("#keywordSearch").addEventListener("input", (event) => {
  state.search = event.target.value;
  renderTable();
});

loadLatest();

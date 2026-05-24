const sampleRows = [
  {
    "콘텐츠명(주제)": "샘플",
    "하위_키워드": "샘플 결말 해석",
    "추천요약": "공략 우선",
    "분석기준수요(월간)": 120000,
    "키워드검색수요(월간_직접)": 80000,
    "총문서량(네이버)": 250,
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
    "유튜브_상태": "측정완료"
  }
];

let rows = [];

const number = (value) => {
  const n = Number(String(value ?? "0").replace(/,/g, ""));
  return Number.isFinite(n) ? n : 0;
};

const isGolden = (row) => row["황금키워드"] === "Y" || row.is_golden === true;

const getKeyword = (row) => row["하위_키워드"] || row.keyword || "";
const getDemand = (row) => number(row["분석기준수요(월간)"] || row["통합검색수요(전체)"] || row.total_demand);
const getDirectDemand = (row) => number(row["키워드검색수요(월간_직접)"] || row.keyword_demand);
const getDocs = (row) => number(row["총문서량(네이버)"] || row.naver_docs);
const getScore = (row) => number(row["기회점수(0-100)"] || row["기회점수"] || row.score);
const getConfidence = (row) => number(row["신뢰도(0-100)"] || row["신뢰도"] || row.confidence);
const getNaverSaturation = (row) => row["네이버_포화율(%)"] ?? row["네이버_포화율"] ?? "";

function parseCsv(text) {
  const clean = text.replace(/^\uFEFF/, "");
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
    if (char === '"' && quoted && next === '"') {
      current += '"';
      i += 1;
    } else if (char === '"') {
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

async function loadLatest() {
  try {
    const response = await fetch("../results/latest_portfolio.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    rows = payload.rows || payload;
  } catch (error) {
    rows = sampleRows;
  }
  render();
}

function handleUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const text = String(reader.result || "");
    if (file.name.endsWith(".json")) {
      const payload = JSON.parse(text);
      rows = payload.rows || payload;
    } else {
      rows = parseCsv(text);
    }
    render();
  };
  reader.readAsText(file, "utf-8");
}

function render() {
  const total = rows.length;
  const golden = rows.filter(isGolden).length;
  const avgConfidence = total ? Math.round(rows.reduce((sum, row) => sum + getConfidence(row), 0) / total) : 0;
  const bestScore = total ? Math.max(...rows.map(getScore)) : 0;

  document.querySelector("#metricTotal").textContent = total.toLocaleString("ko-KR");
  document.querySelector("#metricGolden").textContent = golden.toLocaleString("ko-KR");
  document.querySelector("#metricConfidence").textContent = `${avgConfidence}`;
  document.querySelector("#metricScore").textContent = `${bestScore}`;

  renderFunnel(total, golden);
  renderMatrix();
  renderTable();
  renderStatus();
}

function renderFunnel(total, golden) {
  const directDemand = rows.filter((row) => String(row["키워드수요_상태"] || row.keyword_demand_status || "").includes("측정")).length;
  const measured = rows.filter((row) => (row["네이버_상태"] || row.naver_status) && String(row["네이버_상태"] || row.naver_status).includes("측정")).length;
  const steps = [
    ["후보 수집", total],
    ["공급 측정", measured],
    ["직접수요 확인", directDemand],
    ["황금 확정", golden],
  ];
  const max = Math.max(1, total);
  document.querySelector("#funnel").innerHTML = steps.map(([label, value], index) => `
    <div class="funnel-step">
      <div class="funnel-label">${label}</div>
      <div class="funnel-bar">
        <div class="funnel-fill" style="width:${Math.max(3, (value / max) * 100)}%; background:${["#2867c7", "#14a66a", "#c98912", "#d83f4c"][index]}"></div>
      </div>
      <div class="funnel-value">${value}</div>
    </div>
  `).join("");
}

function renderMatrix() {
  const svg = document.querySelector("#matrix");
  const maxDemand = Math.max(1, ...rows.map(getDemand));
  const maxDocs = Math.max(1, ...rows.map(getDocs));
  const plot = rows.slice(0, 80).map((row) => {
    const x = 72 + (Math.log10(getDemand(row) + 1) / Math.log10(maxDemand + 1)) * 500;
    const y = 298 - (Math.log10(getDocs(row) + 1) / Math.log10(maxDocs + 1)) * 230;
    const fill = isGolden(row) ? "#c98912" : getScore(row) >= 50 ? "#2867c7" : "#8b97a7";
    const label = getKeyword(row).replace(/[<>&]/g, "");
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

function renderTable() {
  const ranked = [...rows]
    .sort((a, b) => Number(isGolden(b)) - Number(isGolden(a)) || getScore(b) - getScore(a))
    .slice(0, 12);
  document.querySelector("#keywordRows").innerHTML = ranked.map((row) => `
    <tr>
      <td><strong>${getKeyword(row)}</strong><br><span>${row["콘텐츠명(주제)"] || ""}</span></td>
      <td><span class="badge ${isGolden(row) ? "gold" : ""}">${row["추천요약"] || (isGolden(row) ? "공략 우선" : "검토")}</span></td>
      <td>${getDirectDemand(row) ? getDirectDemand(row).toLocaleString("ko-KR") : "-"}</td>
      <td>${getNaverSaturation(row) === "" ? "-" : `${getNaverSaturation(row)}%`}</td>
      <td>${getScore(row)} / ${getConfidence(row)}</td>
      <td>${row["판정근거"] || ""}</td>
    </tr>
  `).join("");
}

function renderStatus() {
  const keys = ["키워드수요_상태", "수요상태", "네이버_상태", "다음_상태", "유튜브_상태"];
  const items = keys.map((key) => {
    const counts = rows.reduce((acc, row) => {
      const value = row[key] || "미기록";
      acc[value] = (acc[value] || 0) + 1;
      return acc;
    }, {});
    const detail = Object.entries(counts).map(([name, count]) => `${name} ${count}`).join(" · ");
    const ok = Object.keys(counts).some((name) => name.includes("측정완료"));
    return `
      <div class="status-item">
        <div><strong>${key}</strong><br><span>${detail}</span></div>
        <span class="badge ${ok ? "ok" : "warn"}">${ok ? "OK" : "CHECK"}</span>
      </div>
    `;
  }).join("");
  document.querySelector("#statusList").innerHTML = items;
}

document.querySelector("#loadLatest").addEventListener("click", loadLatest);
document.querySelector("#fileInput").addEventListener("change", handleUpload);
loadLatest();

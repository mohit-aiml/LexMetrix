/**
 * LexMetrix - Frontend Application Logic
 * Implements scan workflow, computer vision review, rule checklist rendering,
 * chart analytics, and mobile field inspector simulator.
 */

// Global state
let currentActiveTab = "scanner";
let selectedFileBlob = null;
let selectedSampleId = null;
let cameraStream = null;
let isMobileMode = false;
let violationsChartInstance = null;
let categoryChartInstance = null;

// Initialize when DOM loaded
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  loadSamples();
  setupDragAndDrop();
  loadRepositoryData();
  refreshDashboard();
  loadRulesConfig();
});

// ================= NAVIGATION =================
function switchTab(tabName) {
  currentActiveTab = tabName;
  const tabs = ["scanner", "dashboard", "repository", "rules"];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-content-${t}`);
    
    if (t === tabName) {
      btn.classList.add("active-tab");
      btn.classList.remove("text-slate-300");
      content.classList.remove("hidden");
    } else {
      btn.classList.remove("active-tab");
      btn.classList.add("text-slate-300");
      content.classList.add("hidden");
    }
  });

  if (tabName === "dashboard") {
    refreshDashboard();
  } else if (tabName === "repository") {
    loadRepositoryData();
  } else if (tabName === "rules") {
    loadRulesConfig();
  }

  if (window.lucide) lucide.createIcons();
}

function toggleMobileViewport() {
  isMobileMode = !isMobileMode;
  const body = document.body;
  const label = document.getElementById("mobile-toggle-text");
  
  if (isMobileMode) {
    body.classList.add("mobile-mode");
    label.innerText = "Desktop View";
  } else {
    body.classList.remove("mobile-mode");
    label.innerText = "Mobile View";
  }
}

// ================= SAMPLE PRESETS =================
async function loadSamples() {
  try {
    const res = await fetch("/api/samples");
    const samples = await res.json();
    const container = document.getElementById("sample-cards-grid");
    container.innerHTML = "";

    samples.forEach(s => {
      const badgeColor = s.expected_verdict === "COMPLIANT" ? "bg-emerald-100 text-emerald-800 border-emerald-300" :
                         s.expected_verdict === "NON_COMPLIANT" ? "bg-red-100 text-red-800 border-red-300" :
                         "bg-amber-100 text-amber-800 border-amber-300";

      const card = document.createElement("div");
      card.className = "bg-slate-50 hover:bg-white border border-slate-200 hover:border-blue-400 rounded-xl p-3 cursor-pointer transition shadow-xs hover:shadow-md flex flex-col justify-between";
      card.onclick = () => selectSample(s);

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeColor}">
              ${s.expected_verdict}
            </span>
          </div>
          <h4 class="text-xs font-bold text-slate-800 leading-snug line-clamp-1">${s.name}</h4>
          <p class="text-[11px] text-slate-500 line-clamp-2 mt-1">${s.description}</p>
        </div>
        <div class="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-blue-600 font-semibold">
          <span>Click to Test</span>
          <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to load sample cards:", err);
  }
}

function selectSample(sample) {
  selectedSampleId = sample.id;
  selectedFileBlob = null;

  document.getElementById("meta-product-name").value = sample.name;
  document.getElementById("meta-brand").value = sample.brand;
  document.getElementById("meta-category").value = sample.category;

  // Show preview
  const previewCard = document.getElementById("selected-preview-card");
  const previewImg = document.getElementById("selected-preview-img");
  const previewName = document.getElementById("selected-preview-name");
  const previewSize = document.getElementById("selected-preview-size");

  previewImg.src = sample.image_url;
  previewName.innerText = sample.name;
  previewSize.innerText = "Pre-loaded packaging test scenario";
  previewCard.classList.remove("hidden");

  // Auto trigger scan
  executeScan();
}

// ================= DRAG AND DROP & UPLOAD =================
function setupDragAndDrop() {
  const dropZone = document.getElementById("drop-zone");
  
  ["dragenter", "dragover"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      dropZone.classList.add("border-blue-500", "bg-blue-50/40");
    });
  });

  ["dragleave", "drop"].forEach(event => {
    dropZone.addEventListener(event, (e) => {
      e.preventDefault();
      dropZone.classList.remove("border-blue-500", "bg-blue-50/40");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleUploadedFile(files[0]);
    }
  });
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (file) {
    handleUploadedFile(file);
  }
}

function handleUploadedFile(file) {
  selectedFileBlob = file;
  selectedSampleId = null;

  const previewCard = document.getElementById("selected-preview-card");
  const previewImg = document.getElementById("selected-preview-img");
  const previewName = document.getElementById("selected-preview-name");
  const previewSize = document.getElementById("selected-preview-size");

  previewName.innerText = file.name;
  previewSize.innerText = `${(file.size / 1024).toFixed(1)} KB • Image Ingested`;
  previewImg.src = URL.createObjectURL(file);
  previewCard.classList.remove("hidden");

  // Auto set product name guess from filename
  const cleanName = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
  document.getElementById("meta-product-name").value = cleanName;
}

function clearSelectedImage() {
  selectedFileBlob = null;
  selectedSampleId = null;
  document.getElementById("selected-preview-card").classList.add("hidden");
  document.getElementById("file-input").value = "";
}

// ================= LIVE CAMERA CAPTURE =================
function setCaptureMode(mode) {
  const uploadPanel = document.getElementById("upload-panel");
  const cameraPanel = document.getElementById("camera-panel");
  const uploadBtn = document.getElementById("mode-upload-btn");
  const cameraBtn = document.getElementById("mode-camera-btn");

  if (mode === "camera") {
    uploadPanel.classList.add("hidden");
    cameraPanel.classList.remove("hidden");
    uploadBtn.className = "px-2.5 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900";
    cameraBtn.className = "px-2.5 py-1 rounded-md font-medium bg-white text-slate-900 shadow-xs";
    startCamera();
  } else {
    stopCamera();
    cameraPanel.classList.add("hidden");
    uploadPanel.classList.remove("hidden");
    cameraBtn.className = "px-2.5 py-1 rounded-md font-medium text-slate-600 hover:text-slate-900";
    uploadBtn.className = "px-2.5 py-1 rounded-md font-medium bg-white text-slate-900 shadow-xs";
  }
}

async function startCamera() {
  try {
    const video = document.getElementById("camera-feed");
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" }
    });
    video.srcObject = cameraStream;
  } catch (err) {
    alert("Camera access was not granted or is unavailable: " + err.message);
    setCaptureMode("upload");
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
}

function captureFromCamera() {
  const video = document.getElementById("camera-feed");
  if (!video) return;

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob((blob) => {
    selectedFileBlob = blob;
    selectedSampleId = null;

    const previewCard = document.getElementById("selected-preview-card");
    const previewImg = document.getElementById("selected-preview-img");
    const previewName = document.getElementById("selected-preview-name");
    const previewSize = document.getElementById("selected-preview-size");

    previewName.innerText = "Camera_Capture_" + Date.now() + ".png";
    previewSize.innerText = `${(blob.size / 1024).toFixed(1)} KB • Captured from Lens`;
    previewImg.src = URL.createObjectURL(blob);
    previewCard.classList.remove("hidden");

    stopCamera();
    setCaptureMode("upload");
  }, "image/png");
}

// ================= SCAN & COMPLIANCE EXECUTION =================
async function executeScan() {
  if (!selectedFileBlob && !selectedSampleId) {
    alert("Please select a sample scenario or upload a product packaging image first.");
    return;
  }

  const statusBox = document.getElementById("pipeline-status");
  const statusText = document.getElementById("pipeline-status-text");
  const stepBadge = document.getElementById("pipeline-step-badge");
  const progressBar = document.getElementById("pipeline-progress-bar");
  const scanBtn = document.getElementById("run-scan-btn");

  statusBox.classList.remove("hidden");
  scanBtn.disabled = true;
  scanBtn.classList.add("opacity-60");

  const formData = new FormData();
  if (selectedSampleId) {
    formData.append("sample_id", selectedSampleId);
  } else if (selectedFileBlob) {
    formData.append("file", selectedFileBlob, "package_scan.png");
  }

  formData.append("product_name", document.getElementById("meta-product-name").value);
  formData.append("brand", document.getElementById("meta-brand").value);
  formData.append("category", document.getElementById("meta-category").value);
  formData.append("location", document.getElementById("meta-location").value);

  // Step 1: Preprocessing & Blur Analysis
  statusText.innerText = "Step 1: Ingesting image & running CLAHE contrast enhancement...";
  stepBadge.innerText = "Step 1/4";
  progressBar.style.width = "25%";

  await new Promise(r => setTimeout(r, 200));

  // Step 2: OCR Extraction
  statusText.innerText = "Step 2: Running WinRT OCR & bounding box localization...";
  stepBadge.innerText = "Step 2/4";
  progressBar.style.width = "50%";

  try {
    const response = await fetch("/api/scan", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Scan failed with status ${response.status}`);
    }

    // Step 3: Statutory Rule Engine
    statusText.innerText = "Step 3: Evaluating against Legal Metrology Rules, 2011...";
    stepBadge.innerText = "Step 3/4";
    progressBar.style.width = "75%";
    await new Promise(r => setTimeout(r, 200));

    // Step 4: Generating Report & Artifacts
    statusText.innerText = "Step 4: Compiling digital inspection report & Section 36 notice...";
    stepBadge.innerText = "Step 4/4";
    progressBar.style.width = "100%";

    const result = await response.json();
    renderInspectionResults(result);

  } catch (error) {
    alert("Error executing scan: " + error.message);
    console.error(error);
  } finally {
    setTimeout(() => {
      statusBox.classList.add("hidden");
      scanBtn.disabled = false;
      scanBtn.classList.remove("opacity-60");
    }, 400);
  }
}

// ================= RENDER SCAN RESULTS =================
function renderInspectionResults(data) {
  document.getElementById("results-empty-state").classList.add("hidden");
  document.getElementById("results-active-container").classList.remove("hidden");

  // 1. Verdict Banner
  const status = data.compliance_status;
  const score = data.compliance_score;
  const banner = document.getElementById("verdict-banner-card");
  const title = document.getElementById("verdict-status-title");
  const subtitle = document.getElementById("verdict-subtitle");
  const scoreBadge = document.getElementById("verdict-score-badge");
  const iconContainer = document.getElementById("verdict-icon-container");

  if (status === "COMPLIANT") {
    banner.className = "rounded-2xl p-5 border shadow-sm transition bg-emerald-50/70 border-emerald-300 text-emerald-950";
    iconContainer.className = "w-12 h-12 rounded-xl flex items-center justify-center text-white bg-emerald-600";
    title.innerText = "COMPLIANT";
    title.className = "text-xl font-black tracking-tight text-emerald-900";
    scoreBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-extrabold font-mono bg-emerald-200 text-emerald-900";
    subtitle.innerText = "All mandatory declarations meet Legal Metrology (PC) Rules, 2011";
  } else if (status === "NON_COMPLIANT") {
    banner.className = "rounded-2xl p-5 border shadow-sm transition bg-red-50/70 border-red-300 text-red-950";
    iconContainer.className = "w-12 h-12 rounded-xl flex items-center justify-center text-white bg-red-600";
    title.innerText = "NON-COMPLIANT";
    title.className = "text-xl font-black tracking-tight text-red-900";
    scoreBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-extrabold font-mono bg-red-200 text-red-900";
    subtitle.innerText = `${data.violations.length} statutory violation(s) flagged under Legal Metrology Act, 2009`;
  } else {
    banner.className = "rounded-2xl p-5 border shadow-sm transition bg-amber-50/70 border-amber-300 text-amber-950";
    iconContainer.className = "w-12 h-12 rounded-xl flex items-center justify-center text-white bg-amber-500";
    title.innerText = "REVIEW RECOMMENDED";
    title.className = "text-xl font-black tracking-tight text-amber-900";
    scoreBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-extrabold font-mono bg-amber-200 text-amber-900";
    subtitle.innerText = "Minor technical packaging defects or blur detected; advisory notice recommended";
  }
  scoreBadge.innerText = `${score}%`;

  // Legal Recommendation Notice
  const rec = data.legal_recommendation || {};
  document.getElementById("legal-order-title").innerText = `Official Action: ${rec.title || 'Clearance'}`;
  document.getElementById("legal-order-text").innerText = rec.statutory_order || "Inspection recorded.";

  // PDF Link
  document.getElementById("download-pdf-btn").href = data.pdf_report_url;

  // 2. Evidence Image Display
  const evidenceImg = document.getElementById("evidence-display-img");
  evidenceImg.src = data.annotated_image_url || data.image_url;

  // 3. Metrics
  const q = data.quality_metrics || {};
  document.getElementById("metric-blur-score").innerText = `${q.blur_score || 0} (${q.quality_verdict || 'Good'})`;
  const pdp = data.pdp_info || {};
  document.getElementById("metric-pdp-area").innerText = `~${pdp.estimated_area_cm2 || 250} cm²`;
  const summary = data.summary || {};
  document.getElementById("metric-font-height").innerText = `${summary.measured_font_mm || 3.5} mm (Req: ≥${summary.prescribed_min_font_mm || 2.0} mm)`;

  // 4. Checklist Breakdown
  renderStatutoryChecklist(data);

  // 5. Violations List
  renderViolationsList(data.violations);

  if (window.lucide) lucide.createIcons();
}

function renderStatutoryChecklist(data) {
  const container = document.getElementById("statutory-checklist-container");
  container.innerHTML = "";

  const ext = data.extracted_data || {};
  const evals = data.rule_evaluations || [];
  const evalMap = {};
  evals.forEach(e => evalMap[e.rule_id] = e);

  const checklistItems = [
    {
      rule_id: "RULE_6_1_A_MFG",
      title: "Rule 6(1)(a) — Manufacturer / Packer / Importer Details",
      required: "Name & complete postal address with 6-digit PIN code",
      found: ext.manufacturer?.company_name ? `${ext.manufacturer.company_name} (PIN: ${ext.manufacturer.pincode || 'MISSING'})` : "Declaration not detected",
      status: evalMap["RULE_6_1_A_MFG"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_6_1_B_ORIGIN",
      title: "Rule 6(1)(b) — Country of Origin",
      required: "Explicit 'Country of Origin' or 'Made in India' statement",
      found: ext.origin?.country ? `Declared: ${ext.origin.country}` : "Not declared conspicuously",
      status: evalMap["RULE_6_1_B_ORIGIN"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_6_1_C_NET_QTY",
      title: "Rule 6(1)(c) — Net Quantity & Metric Symbols",
      required: "Standard SI symbols (g, kg, ml, l, N). Words 'gms', 'ltrs' prohibited",
      found: ext.net_quantity?.value ? `${ext.net_quantity.value} ${ext.net_quantity.unit}` : "Not detected",
      status: evalMap["RULE_6_1_C_NET_QTY"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_6_1_D_DATE",
      title: "Rule 6(1)(d) — Month and Year of Manufacture / Packing",
      required: "Month & Year of Mfg or Packing (MM/YYYY or Month YYYY)",
      found: ext.dates?.mfg_date ? `Declared: ${ext.dates.mfg_date}` : "Not detected",
      status: evalMap["RULE_6_1_D_DATE"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_6_1_E_MRP",
      title: "Rule 6(1)(e) — MRP & Tax Disclaimer",
      required: "MRP ₹ XX.XX with mandatory '(incl. of all taxes)' disclaimer",
      found: ext.mrp?.amount ? `₹${ext.mrp.amount} (Taxes Declared: ${ext.mrp.has_inclusive_taxes ? 'YES' : 'NO'})` : "Not detected",
      status: evalMap["RULE_6_1_E_MRP"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_6_1_N_CONSUMER_CARE",
      title: "Rule 6(1)(n) — Consumer Care Grievance Details",
      required: "4 Pillars: Contact Person/Designation, Address, Phone & Email",
      found: `Helpline: ${ext.consumer_care?.phone || 'None'} | Email: ${ext.consumer_care?.email || 'None'}`,
      status: evalMap["RULE_6_1_N_CONSUMER_CARE"]?.status || "FAIL"
    },
    {
      rule_id: "RULE_5_FONT_SIZE",
      title: "Rule 5 & First Schedule — Minimum Numeral / Letter Height",
      required: "Mandated height based on net quantity (Table 1)",
      found: `Estimated numeral height: ~${ext.net_quantity?.estimated_height_mm || 3.5}mm`,
      status: evalMap["RULE_5_FONT_SIZE"]?.status || "PASS"
    }
  ];

  checklistItems.forEach(item => {
    let badgeClass = "bg-emerald-100 text-emerald-800 border-emerald-300";
    let statusText = "PASS";
    let iconName = "check";

    if (item.status === "FAIL") {
      badgeClass = "bg-red-100 text-red-800 border-red-300";
      statusText = "FAIL";
      iconName = "x";
    } else if (item.status === "WARN") {
      badgeClass = "bg-amber-100 text-amber-800 border-amber-300";
      statusText = "DEFECT";
      iconName = "alert-circle";
    }

    const row = document.createElement("div");
    row.className = "py-3 highlight-row flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs";
    row.innerHTML = `
      <div class="flex-1">
        <p class="font-bold text-slate-800">${item.title}</p>
        <p class="text-[11px] text-slate-500 mt-0.5"><span class="font-medium text-slate-700">Required:</span> ${item.required}</p>
        <p class="text-[11px] font-mono text-slate-600 mt-0.5"><span class="font-medium text-slate-700">Detected:</span> ${item.found}</p>
      </div>
      <div class="flex items-center">
        <span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-bold border ${badgeClass}">
          <i data-lucide="${iconName}" class="w-3.5 h-3.5"></i>
          <span>${statusText}</span>
        </span>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderViolationsList(violations) {
  const section = document.getElementById("violations-section");
  const container = document.getElementById("violations-list-container");

  if (!violations || violations.length === 0) {
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");
  container.innerHTML = "";

  violations.forEach((v, idx) => {
    const card = document.createElement("div");
    card.className = "bg-white p-3.5 rounded-xl border border-red-200 text-xs shadow-xs space-y-1.5";
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-red-900">${idx + 1}. ${v.rule_title}</span>
        <span class="bg-red-100 text-red-800 text-[10px] font-extrabold px-2 py-0.5 rounded uppercase">${v.severity}</span>
      </div>
      <p class="text-slate-700 font-medium">${v.issue}</p>
      <div class="bg-red-50 p-2 rounded-lg text-[11px] text-red-800 font-mono">
        <span class="font-bold">Statutory Citation:</span> ${v.legal_citation}<br/>
        <span class="font-bold">Applicable Penalty:</span> ${v.penalty_section}
      </div>
    `;
    container.appendChild(card);
  });
}

function shareOrCopySummary() {
  const status = document.getElementById("verdict-status-title").innerText;
  const score = document.getElementById("verdict-score-badge").innerText;
  const prod = document.getElementById("meta-product-name").value;
  const text = `LexMetrix Compliance Inspection Result:\nProduct: ${prod}\nVerdict: ${status} (${score})\nSystem: Legal Metrology (PC) Rules, 2011 Verified.`;
  navigator.clipboard.writeText(text).then(() => {
    alert("Compliance summary copied to clipboard!");
  });
}

// ================= DASHBOARD ANALYTICS =================
async function refreshDashboard() {
  try {
    const [statsRes, recentRes] = await Promise.all([
      fetch("/api/dashboard/stats"),
      fetch("/api/inspections?limit=8")
    ]);

    const stats = await statsRes.json();
    const recent = await recentRes.json();

    // KPIs
    document.getElementById("kpi-total").innerText = stats.total_inspections || 0;
    document.getElementById("kpi-compliance-rate").innerText = `${stats.compliance_rate || 0}%`;
    document.getElementById("kpi-violations").innerText = stats.violation_count || 0;
    document.getElementById("kpi-reviews").innerText = stats.review_count || 0;

    // Violations Bar Chart
    renderViolationsChart(stats.violation_by_rule || {});

    // Category Doughnut Chart
    renderCategoryChart(stats.category_breakdown || {});

    // Recent Table
    renderRecentTable(recent);

  } catch (err) {
    console.error("Dashboard refresh error:", err);
  }
}

function renderViolationsChart(violationsMap) {
  const ctx = document.getElementById("violationsRuleChart");
  if (!ctx) return;

  const ruleLabels = {
    "RULE_6_1_E_MRP": "Rule 6(1)(e) MRP & Taxes",
    "RULE_6_1_N_CONSUMER_CARE": "Rule 6(1)(n) Consumer Care",
    "RULE_6_1_C_NET_QTY": "Rule 6(1)(c) Non-Std Units",
    "RULE_6_1_A_MFG": "Rule 6(1)(a) Mfg & PIN",
    "RULE_5_FONT_SIZE": "Rule 5 Font Size",
    "RULE_6_1_B_ORIGIN": "Rule 6(1)(b) Country Origin"
  };

  const labels = Object.keys(violationsMap).map(k => ruleLabels[k] || k);
  const values = Object.values(violationsMap);

  if (violationsChartInstance) {
    violationsChartInstance.destroy();
  }

  violationsChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.length > 0 ? labels : ["Rule 6(1)(e) MRP", "Rule 6(1)(n) Consumer Care", "Rule 6(1)(c) Units"],
      datasets: [{
        label: "Violations Recorded",
        data: values.length > 0 ? values : [4, 3, 2],
        backgroundColor: "rgba(220, 38, 38, 0.75)",
        borderColor: "rgb(220, 38, 38)",
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0, font: { size: 11 } } },
        x: { ticks: { font: { size: 10 } } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function renderCategoryChart(categoriesMap) {
  const ctx = document.getElementById("categoryPieChart");
  if (!ctx) return;

  const labels = Object.keys(categoriesMap);
  const values = Object.values(categoriesMap);

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels.length > 0 ? labels : ["Biscuits & Confectionery", "Snacks", "Detergents", "Edible Oils"],
      datasets: [{
        data: values.length > 0 ? values : [35, 25, 20, 20],
        backgroundColor: [
          "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B"
        ],
        borderWidth: 2,
        borderColor: "#FFFFFF"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { boxWidth: 12, font: { size: 10 } } }
      }
    }
  });
}

function renderRecentTable(items) {
  const tbody = document.getElementById("dashboard-recent-table-body");
  tbody.innerHTML = "";

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-slate-400">No inspections recorded yet. Click "Seed Enforcement Data" above to populate!</td></tr>`;
    return;
  }

  items.forEach(it => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition";
    
    const badgeColor = it.compliance_status === "COMPLIANT" ? "bg-emerald-100 text-emerald-800" :
                       it.compliance_status === "NON_COMPLIANT" ? "bg-red-100 text-red-800" :
                       "bg-amber-100 text-amber-800";

    tr.innerHTML = `
      <td class="py-2.5 px-3 font-mono font-bold text-slate-800">${it.inspection_code}</td>
      <td class="py-2.5 px-3 text-slate-500">${it.timestamp.substring(0, 16)}</td>
      <td class="py-2.5 px-3 font-medium text-slate-800">${it.product_name}</td>
      <td class="py-2.5 px-3 text-slate-600">${it.category}</td>
      <td class="py-2.5 px-3 text-slate-600">${it.inspector_name}</td>
      <td class="py-2.5 px-3">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeColor}">
          ${it.compliance_status} (${it.compliance_score}%)
        </span>
      </td>
      <td class="py-2.5 px-3 text-right">
        <a href="${it.pdf_report_url}" target="_blank" class="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 font-semibold">
          <i data-lucide="file-text" class="w-3.5 h-3.5"></i>
          <span>PDF</span>
        </a>
      </td>
    `;
    tbody.appendChild(tr);
  });

  if (window.lucide) lucide.createIcons();
}

// ================= REPOSITORY TAB =================
async function loadRepositoryData() {
  const query = document.getElementById("repo-search-input")?.value || "";
  const status = document.getElementById("repo-status-filter")?.value || "ALL";
  const category = document.getElementById("repo-category-filter")?.value || "ALL";

  try {
    const res = await fetch(`/api/inspections?query=${encodeURIComponent(query)}&status=${status}&category=${encodeURIComponent(category)}`);
    const records = await res.json();
    const tbody = document.getElementById("repository-table-body");
    tbody.innerHTML = "";

    if (!records || records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-400">No inspections match current criteria.</td></tr>`;
      return;
    }

    records.forEach(r => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      
      const badgeColor = r.compliance_status === "COMPLIANT" ? "bg-emerald-100 text-emerald-800" :
                         r.compliance_status === "NON_COMPLIANT" ? "bg-red-100 text-red-800" :
                         "bg-amber-100 text-amber-800";

      tr.innerHTML = `
        <td class="py-3 px-4 font-mono font-bold text-slate-800">${r.inspection_code}</td>
        <td class="py-3 px-4 text-slate-500">${r.timestamp}</td>
        <td class="py-3 px-4 font-semibold text-slate-800">${r.product_name}<div class="text-[10px] text-slate-400 font-normal">${r.brand}</div></td>
        <td class="py-3 px-4 text-slate-600">${r.category}</td>
        <td class="py-3 px-4 text-slate-500">${r.location}</td>
        <td class="py-3 px-4 font-mono font-bold">${r.compliance_score}%</td>
        <td class="py-3 px-4">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${badgeColor}">
            ${r.compliance_status}
          </span>
        </td>
        <td class="py-3 px-4 text-right space-x-2">
          <button onclick='openEvidenceModal(${JSON.stringify(r)})' class="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600" title="View Evidence">
            <i data-lucide="eye" class="w-4 h-4"></i>
          </button>
          <a href="${r.pdf_report_url}" target="_blank" class="p-1.5 inline-block rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700" title="Download Official Report">
            <i data-lucide="download" class="w-4 h-4"></i>
          </a>
        </td>
      `;
      tbody.appendChild(tr);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Repository load error:", err);
  }
}

function openEvidenceModal(record) {
  document.getElementById("modal-title").innerText = record.product_name;
  document.getElementById("modal-code").innerText = `${record.inspection_code} • ${record.timestamp}`;
  document.getElementById("modal-img").src = record.annotated_image_url || record.image_url;
  document.getElementById("modal-status").innerText = record.compliance_status;
  document.getElementById("modal-status").className = `text-sm font-black mt-0.5 ${record.compliance_status === 'COMPLIANT' ? 'text-emerald-700' : 'text-red-700'}`;
  document.getElementById("modal-score").innerText = `Compliance Score: ${record.compliance_score}%`;
  document.getElementById("modal-pdf-link").href = record.pdf_report_url;

  const declContainer = document.getElementById("modal-declarations");
  const ext = record.extracted_data || {};
  declContainer.innerHTML = `
    <div><strong>MRP:</strong> ₹${ext.mrp?.amount || 'N/A'} (${ext.mrp?.has_inclusive_taxes ? 'Taxes Incl' : 'No Taxes Mentioned'})</div>
    <div><strong>Net Quantity:</strong> ${ext.net_quantity?.value || 'N/A'} ${ext.net_quantity?.unit || ''}</div>
    <div><strong>Manufacturer:</strong> ${ext.manufacturer?.company_name || 'N/A'} (PIN: ${ext.manufacturer?.pincode || 'None'})</div>
    <div><strong>Mfg Date:</strong> ${ext.dates?.mfg_date || 'N/A'}</div>
    <div><strong>Helpline:</strong> ${ext.consumer_care?.phone || 'N/A'} | <strong>Email:</strong> ${ext.consumer_care?.email || 'N/A'}</div>
  `;

  document.getElementById("evidence-modal").classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeEvidenceModal() {
  document.getElementById("evidence-modal").classList.add("hidden");
}

// ================= RULES CONFIG TAB =================
async function loadRulesConfig() {
  try {
    const res = await fetch("/api/rules");
    const rules = await res.json();
    const container = document.getElementById("rules-cards-container");
    container.innerHTML = "";

    rules.forEach(rule => {
      const card = document.createElement("div");
      card.className = "bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3";
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div>
            <span class="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">${rule.rule_id}</span>
            <h4 class="text-sm font-bold text-slate-900 mt-1">${rule.rule_name}</h4>
          </div>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${rule.is_mandatory ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}">
            ${rule.is_mandatory ? 'MANDATORY' : 'OPTIONAL'}
          </span>
        </div>
        <p class="text-xs text-slate-600">${rule.description}</p>
        <div class="bg-slate-50 p-3 rounded-xl text-[11px] font-mono border border-slate-100 text-slate-700">
          <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Statutory Clause & Parameters</div>
          <div class="text-slate-900 font-semibold mb-1">${rule.legal_citation}</div>
          <pre class="overflow-x-auto text-[10px] text-slate-600">${JSON.stringify(rule.parameters, null, 2)}</pre>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to load rules:", err);
  }
}

// ================= SEED DEMO DATA =================
async function seedDemoData() {
  try {
    const res = await fetch("/api/seed-demo-data", { method: "POST" });
    const data = await res.json();
    alert(`Successfully seeded ${data.seeded_count} realistic historical enforcement inspections across Indian retail hubs!`);
    refreshDashboard();
    loadRepositoryData();
  } catch (err) {
    alert("Error seeding demo data: " + err.message);
  }
}

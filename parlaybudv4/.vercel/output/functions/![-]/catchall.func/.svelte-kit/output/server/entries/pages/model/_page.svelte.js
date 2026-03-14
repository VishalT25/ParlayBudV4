import { ac as fallback, e as ensure_array_like, ad as attr_style, b as attr, c as escape_html, ae as bind_props, af as stringify, ag as head, a as attr_class } from "../../../chunks/index2.js";
import { c as getStatColor } from "../../../chunks/utils2.js";
function BarChart($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let topData, maxVal;
    let data = $$props["data"];
    let color = fallback($$props["color"], "#3b82f6");
    function formatFeature(f) {
      return f.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }
    topData = data.slice(0, 10);
    maxVal = Math.max(...topData.map((d) => d.importance));
    $$renderer2.push(`<div class="bar-chart svelte-9fnibp"><!--[-->`);
    const each_array = ensure_array_like(topData);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let item = each_array[i];
      const widthPct = item.importance / maxVal * 100;
      $$renderer2.push(`<div class="bar-row svelte-9fnibp"${attr_style(`animation-delay: ${stringify(i * 60)}ms;`)}><div class="feature-label svelte-9fnibp"${attr("title", formatFeature(item.feature))}>${escape_html(formatFeature(item.feature))}</div> <div class="bar-track svelte-9fnibp"><div class="bar-fill svelte-9fnibp"${attr_style(`width: ${stringify(widthPct)}%; background: linear-gradient(90deg, ${stringify(color)}, ${stringify(color)}99);`)}></div></div> <div class="importance-val svelte-9fnibp">${escape_html((item.importance * 100).toFixed(1))}%</div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { data, color });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let metrics;
    let data = $$props["data"];
    let activeImportanceTab = "PTS";
    const thresholds = ["0.55", "0.60", "0.65", "0.70", "0.75"];
    const statList = ["PTS", "REB", "AST"];
    const calibPad = { top: 20, right: 20, bottom: 50, left: 55 };
    const calibCW = 500 - calibPad.left - calibPad.right;
    const calibCH = 280 - calibPad.top - calibPad.bottom;
    const calibTicks = [0.5, 0.6, 0.7, 0.8, 0.9, 1];
    function calibX(prob) {
      return calibPad.left + (prob - 0.5) / 0.5 * calibCW;
    }
    function calibY(rate) {
      return calibPad.top + calibCH - (rate - 0.5) / 0.5 * calibCH;
    }
    metrics = data.metrics;
    head("19jumuq", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>ParlayBud — Model</title>`);
      });
    });
    $$renderer2.push(`<div class="page svelte-19jumuq"><div class="container"><div class="page-title-row svelte-19jumuq"><div><h1 class="page-title svelte-19jumuq">Model Intelligence</h1> <p class="page-subtitle svelte-19jumuq">XGBoost ensemble trained on 3 seasons of NBA game logs</p></div> <div class="model-version-badge svelte-19jumuq"><span class="mv-icon svelte-19jumuq">🤖</span> <span class="mv-text svelte-19jumuq">v4-xgboost</span></div></div> <div class="training-grid svelte-19jumuq"><div class="training-card glass svelte-19jumuq"><div class="tc-icon svelte-19jumuq">📊</div> <div class="tc-val svelte-19jumuq">${escape_html(metrics.training.total_logs.toLocaleString())}</div> <div class="tc-label svelte-19jumuq">Game Logs</div> <div class="tc-sub svelte-19jumuq">Training samples</div></div> <div class="training-card glass svelte-19jumuq"><div class="tc-icon svelte-19jumuq">🏀</div> <div class="tc-val svelte-19jumuq">${escape_html(metrics.training.players)}</div> <div class="tc-label svelte-19jumuq">Players</div> <div class="tc-sub svelte-19jumuq">Tracked athletes</div></div> <div class="training-card glass svelte-19jumuq"><div class="tc-icon svelte-19jumuq">📅</div> <div class="tc-val svelte-19jumuq">${escape_html(metrics.training.seasons)}</div> <div class="tc-label svelte-19jumuq">Seasons</div> <div class="tc-sub svelte-19jumuq">2022–2025</div></div> <div class="training-card glass svelte-19jumuq"><div class="tc-icon svelte-19jumuq">🗓️</div> <div class="tc-val svelte-19jumuq">2+ yrs</div> <div class="tc-label svelte-19jumuq">Data Range</div> <div class="tc-sub svelte-19jumuq">${escape_html(metrics.training.date_range.start)} → ${escape_html(metrics.training.date_range.end)}</div></div></div> <div class="section-card glass svelte-19jumuq"><div class="section-header-bar svelte-19jumuq"><h2 class="section-title svelte-19jumuq"><span class="section-icon svelte-19jumuq">📈</span> Model Performance Metrics</h2> <div class="metrics-legend svelte-19jumuq"><span class="ml-item svelte-19jumuq"><span class="ml-dot svelte-19jumuq" style="background: #3b82f6;"></span> AUC measures discriminative ability</span></div></div> <div class="metrics-table-wrap svelte-19jumuq"><table class="metrics-table svelte-19jumuq"><thead><tr><th class="svelte-19jumuq">Model</th><th class="svelte-19jumuq">AUC</th><th class="svelte-19jumuq">Accuracy</th><th class="svelte-19jumuq">Brier Score</th><th class="svelte-19jumuq">Log Loss</th><th class="svelte-19jumuq">Status</th></tr></thead><tbody><!--[-->`);
    const each_array = ensure_array_like(statList);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let stat = each_array[$$index];
      const m = metrics.models[stat];
      const color = getStatColor(stat);
      $$renderer2.push(`<tr class="metrics-row svelte-19jumuq"><td class="svelte-19jumuq"><span class="stat-pill svelte-19jumuq"${attr_style(`background: ${stringify(color)}15; color: ${stringify(color)}; border-color: ${stringify(color)}30;`)}>${escape_html(stat)}</span></td><td class="svelte-19jumuq"><div class="metric-with-bar svelte-19jumuq"><span class="metric-val svelte-19jumuq">${escape_html(m.auc.toFixed(3))}</span> <div class="metric-bar-track svelte-19jumuq"><div class="metric-bar-fill svelte-19jumuq"${attr_style(`width: ${stringify(m.auc * 100)}%; background: ${stringify(color)};`)}></div></div></div></td><td class="svelte-19jumuq"><span class="metric-val highlight svelte-19jumuq"${attr_style(`color: ${stringify(color)};`)}>${escape_html((m.accuracy * 100).toFixed(1))}%</span></td><td class="svelte-19jumuq"><span class="metric-val svelte-19jumuq">${escape_html(m.brier_score.toFixed(3))}</span></td><td class="svelte-19jumuq"><span class="metric-val svelte-19jumuq">${escape_html(m.log_loss.toFixed(3))}</span></td><td class="svelte-19jumuq"><span class="status-good svelte-19jumuq">✓ Production</span></td></tr>`);
    }
    $$renderer2.push(`<!--]--></tbody></table></div></div> <div class="section-card glass svelte-19jumuq"><div class="section-header-bar svelte-19jumuq"><h2 class="section-title svelte-19jumuq"><span class="section-icon svelte-19jumuq">🎯</span> Hit Rate by Confidence Threshold</h2> <div class="threshold-note svelte-19jumuq">Higher threshold = fewer but more accurate picks</div></div> <div class="threshold-table-wrap svelte-19jumuq"><table class="threshold-table svelte-19jumuq"><thead><tr><th class="svelte-19jumuq">Threshold</th><!--[-->`);
    const each_array_1 = ensure_array_like(statList);
    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
      let stat = each_array_1[$$index_1];
      $$renderer2.push(`<th${attr_style(`color: ${stringify(getStatColor(stat))};`)} class="svelte-19jumuq">${escape_html(stat)}</th>`);
    }
    $$renderer2.push(`<!--]--><th class="svelte-19jumuq">Interpretation</th></tr></thead><tbody><!--[-->`);
    const each_array_2 = ensure_array_like(thresholds);
    for (let $$index_3 = 0, $$length = each_array_2.length; $$index_3 < $$length; $$index_3++) {
      let thresh = each_array_2[$$index_3];
      $$renderer2.push(`<tr${attr_class("thresh-row svelte-19jumuq", void 0, { "highlight-row": thresh === "0.70" })}><td class="svelte-19jumuq"><span${attr_class("thresh-badge svelte-19jumuq", void 0, { "target": thresh === "0.70" })}>${escape_html((parseFloat(thresh) * 100).toFixed(0))}%+ `);
      if (thresh === "0.70") {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="target-tag svelte-19jumuq">TARGET</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></span></td><!--[-->`);
      const each_array_3 = ensure_array_like(statList);
      for (let $$index_2 = 0, $$length2 = each_array_3.length; $$index_2 < $$length2; $$index_2++) {
        let stat = each_array_3[$$index_2];
        const rate = metrics.models[stat].hit_rates[thresh];
        $$renderer2.push(`<td class="svelte-19jumuq"><span class="rate-cell svelte-19jumuq"${attr_style(`color: ${stringify(rate >= 0.7 ? "#22c55e" : rate >= 0.65 ? "#f59e0b" : "#94a3b8")};`)}>${escape_html((rate * 100).toFixed(1))}%</span></td>`);
      }
      $$renderer2.push(`<!--]--><td class="interp-cell svelte-19jumuq">`);
      if (thresh === "0.55") {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`Baseline filter`);
      } else if (thresh === "0.60") {
        $$renderer2.push("<!--[1-->");
        $$renderer2.push(`Standard picks`);
      } else if (thresh === "0.65") {
        $$renderer2.push("<!--[2-->");
        $$renderer2.push(`High confidence`);
      } else if (thresh === "0.70") {
        $$renderer2.push("<!--[3-->");
        $$renderer2.push(`Locks threshold`);
      } else {
        $$renderer2.push("<!--[-1-->");
        $$renderer2.push(`Elite only`);
      }
      $$renderer2.push(`<!--]--></td></tr>`);
    }
    $$renderer2.push(`<!--]--></tbody></table></div></div> <div class="section-card glass svelte-19jumuq"><div class="section-header-bar svelte-19jumuq"><h2 class="section-title svelte-19jumuq"><span class="section-icon svelte-19jumuq">🔬</span> Feature Importance</h2> <div class="importance-tabs svelte-19jumuq"><!--[-->`);
    const each_array_4 = ensure_array_like(statList);
    for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
      let stat = each_array_4[$$index_4];
      $$renderer2.push(`<button${attr_class("imp-tab svelte-19jumuq", void 0, { "active": activeImportanceTab === stat })}${attr_style(activeImportanceTab === stat ? `color: ${getStatColor(stat)}; border-color: ${getStatColor(stat)}30; background: ${getStatColor(stat)}10;` : "")}>${escape_html(stat)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="importance-content svelte-19jumuq">`);
    BarChart($$renderer2, {
      data: metrics.feature_importance[activeImportanceTab],
      color: getStatColor(activeImportanceTab)
    });
    $$renderer2.push(`<!----></div></div> <div class="section-card glass svelte-19jumuq"><div class="section-header-bar svelte-19jumuq"><h2 class="section-title svelte-19jumuq"><span class="section-icon svelte-19jumuq">⚖️</span> Model Calibration (PTS)</h2> <div class="calib-note svelte-19jumuq">Predicted probability vs actual hit rate — closer to diagonal = better calibration</div></div> <div class="calibration-wrap svelte-19jumuq"><svg viewBox="0 0 500 280" class="calib-svg svelte-19jumuq" preserveAspectRatio="xMidYMid meet"><!--[-->`);
    const each_array_5 = ensure_array_like(calibTicks);
    for (let $$index_5 = 0, $$length = each_array_5.length; $$index_5 < $$length; $$index_5++) {
      let tick = each_array_5[$$index_5];
      $$renderer2.push(`<line${attr("x1", calibX(tick))}${attr("y1", calibPad.top)}${attr("x2", calibX(tick))}${attr("y2", calibPad.top + calibCH)} stroke="rgba(255,255,255,0.04)" stroke-width="1"></line><line${attr("x1", calibPad.left)}${attr("y1", calibY(tick))}${attr("x2", calibPad.left + calibCW)}${attr("y2", calibY(tick))} stroke="rgba(255,255,255,0.04)" stroke-width="1"></line><text${attr("x", calibX(tick))}${attr("y", calibPad.top + calibCH + 18)} text-anchor="middle" fill="#475569" font-size="10" font-family="Inter">${escape_html((tick * 100).toFixed(0))}%</text><text${attr("x", calibPad.left - 8)}${attr("y", calibY(tick) + 4)} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">${escape_html((tick * 100).toFixed(0))}%</text>`);
    }
    $$renderer2.push(`<!--]--><line${attr("x1", calibPad.left)}${attr("y1", calibPad.top + calibCH)}${attr("x2", calibPad.left + calibCW)}${attr("y2", calibPad.top)} stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="6 4"></line><text${attr("x", calibPad.left + calibCW - 2)}${attr("y", calibPad.top + 14)} fill="rgba(255,255,255,0.3)" font-size="10" font-family="Inter" text-anchor="end">Perfect</text><!--[-->`);
    const each_array_6 = ensure_array_like(metrics.calibration.PTS);
    for (let i = 0, $$length = each_array_6.length; i < $$length; i++) {
      let pt = each_array_6[i];
      if (i > 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<line${attr("x1", calibX(metrics.calibration.PTS[i - 1].pred_prob))}${attr("y1", calibY(metrics.calibration.PTS[i - 1].actual_rate))}${attr("x2", calibX(pt.pred_prob))}${attr("y2", calibY(pt.actual_rate))} stroke="#3b82f6" stroke-width="2"></line>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--><circle${attr("cx", calibX(pt.pred_prob))}${attr("cy", calibY(pt.actual_rate))} r="5" fill="#3b82f6" stroke="#0f172a" stroke-width="2" style="filter: drop-shadow(0 0 4px rgba(59,130,246,0.6));"></circle>`);
    }
    $$renderer2.push(`<!--]--><text${attr("x", calibPad.left + calibCW / 2)}${attr("y", 275)} text-anchor="middle" fill="#64748b" font-size="11" font-family="Inter">Predicted Probability</text><text${attr("x", 14)}${attr("y", calibPad.top + calibCH / 2)} text-anchor="middle" fill="#64748b" font-size="11" font-family="Inter"${attr("transform", `rotate(-90, 14, ${stringify(calibPad.top + calibCH / 2)})`)}>Actual Hit Rate</text></svg></div></div> <div class="methodology-card glass svelte-19jumuq"><div class="section-header-bar svelte-19jumuq"><h2 class="section-title svelte-19jumuq"><span class="section-icon svelte-19jumuq">📋</span> Methodology</h2></div> <div class="methodology-content svelte-19jumuq"><div class="meth-grid svelte-19jumuq"><div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">01</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">Data Collection</div> <div class="meth-desc svelte-19jumuq">NBA game logs collected from 2022–2025 across 279 active players. Includes box scores, pace factors, opponent ratings, rest days, and home/away splits.</div></div></div> <div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">02</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">Feature Engineering</div> <div class="meth-desc svelte-19jumuq">Rolling averages (L3, L5, L10, season), matchup difficulty scores, usage rate trends, back-to-back flags, altitude adjustments, and line gap analysis.</div></div></div> <div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">03</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">XGBoost Training</div> <div class="meth-desc svelte-19jumuq">Separate gradient-boosted models for PTS, REB, and AST. Binary classification: will player exceed the sportsbook line? Calibrated with Platt scaling.</div></div></div> <div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">04</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">Edge Calculation</div> <div class="meth-desc svelte-19jumuq">Edge = model probability − implied probability from odds. Only picks with edge > 8% are included. EV calculated using Kelly-inspired formula.</div></div></div> <div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">05</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">Pick Selection</div> <div class="meth-desc svelte-19jumuq">Top picks ranked by EV. Locks = model probability ≥ 70%. Parlays built from highest-probability correlated picks with combined probability displayed.</div></div></div> <div class="meth-item svelte-19jumuq"><div class="meth-step svelte-19jumuq">06</div> <div class="meth-info"><div class="meth-title svelte-19jumuq">Continuous Validation</div> <div class="meth-desc svelte-19jumuq">Results tracked daily. AUC, Brier score, and hit rates monitored for drift. Model retrained monthly with new data. Out-of-sample validation maintained.</div></div></div></div></div></div></div></div>`);
    bind_props($$props, { data });
  });
}
export {
  _page as default
};

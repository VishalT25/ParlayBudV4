import { b as attr, e as ensure_array_like, c as escape_html, ae as bind_props, af as stringify, ag as head, ad as attr_style, a as attr_class } from "../../../chunks/index2.js";
import { h as formatDateShort } from "../../../chunks/utils2.js";
function HitRateChart($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let sorted, points, linePath, areaPath;
    let data = $$props["data"];
    const W = 800;
    const H = 220;
    const PAD = { top: 20, right: 20, bottom: 50, left: 52 };
    const innerW = W - PAD.left - PAD.right;
    const innerH = H - PAD.top - PAD.bottom;
    const yMin = 0.5;
    const yMax = 1;
    function xPos(i) {
      if (sorted.length <= 1) return PAD.left + innerW / 2;
      return PAD.left + i / (sorted.length - 1) * innerW;
    }
    function yPos(val) {
      return PAD.top + innerH - (val - yMin) / (yMax - yMin) * innerH;
    }
    const yTicks = [0.5, 0.6, 0.7, 0.8, 0.9, 1];
    sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
    points = sorted.map((d, i) => ({ x: xPos(i), y: yPos(d.hit_rate), ...d }));
    linePath = (() => {
      if (points.length === 0) return "";
      if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
      let d = `M ${points[0].x} ${points[0].y}`;
      for (let i = 1; i < points.length; i++) {
        const prev = points[i - 1];
        const curr = points[i];
        const cpx = (prev.x + curr.x) / 2;
        d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
      }
      return d;
    })();
    areaPath = (() => {
      if (points.length === 0) return "";
      const bottom = PAD.top + innerH;
      let d = linePath;
      d += ` L ${points[points.length - 1].x} ${bottom} L ${points[0].x} ${bottom} Z`;
      return d;
    })();
    $$renderer2.push(`<div class="chart-container svelte-1ph0zwj"><svg${attr("viewBox", `0 0 ${stringify(
      // Y-axis gridlines
      W
    )} ${stringify(H)}`)} preserveAspectRatio="xMidYMid meet" class="chart-svg svelte-1ph0zwj"><defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b82f6" stop-opacity="0.25"></stop><stop offset="100%" stop-color="#3b82f6" stop-opacity="0"></stop></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"></feGaussianBlur><feMerge><feMergeNode in="blur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge></filter></defs><!--[-->`);
    const each_array = ensure_array_like(yTicks);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tick = each_array[$$index];
      const y = yPos(tick);
      $$renderer2.push(`<line${attr("x1", PAD.left)}${attr("y1", y)}${attr("x2", PAD.left + innerW)}${attr("y2", y)}${attr("stroke", tick === 0.7 ? "rgba(245,158,11,0.4)" : "rgba(255,255,255,0.05)")}${attr("stroke-width", tick === 0.7 ? 1.5 : 1)}${attr("stroke-dasharray", tick === 0.7 ? "6 4" : "0")}></line><text${attr("x", PAD.left - 8)}${attr("y", y + 4)} text-anchor="end" fill="#475569" font-size="11" font-family="Inter, sans-serif">${escape_html((tick * 100).toFixed(0))}%</text>`);
    }
    $$renderer2.push(`<!--]--><text${attr("x", PAD.left + innerW + 4)}${attr("y", yPos(0.7) + 4)} fill="#f59e0b" font-size="10" font-family="Inter, sans-serif" font-weight="600">Target</text>`);
    if (points.length > 1) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<path${attr("d", areaPath)} fill="url(#areaGrad)"></path>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
    if (points.length > 1) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<path${attr("d", linePath)} fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"></path>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--><!--[-->`);
    const each_array_1 = ensure_array_like(points);
    for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
      let pt = each_array_1[i];
      if (i === 0 || i === points.length - 1 || points.length <= 5) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<text${attr("x", pt.x)}${attr("y", PAD.top + innerH + 20)} text-anchor="middle" fill="#475569" font-size="11" font-family="Inter, sans-serif">${escape_html(formatDateShort(pt.date))}</text>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--><!--[-->`);
    const each_array_2 = ensure_array_like(points);
    for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
      let pt = each_array_2[$$index_2];
      $$renderer2.push(`<circle${attr("cx", pt.x)}${attr("cy", pt.y)} r="5"${attr("fill", pt.hit_rate >= 0.7 ? "#22c55e" : pt.hit_rate >= 0.6 ? "#f59e0b" : "#ef4444")} stroke="#0f172a" stroke-width="2" style="cursor: pointer;"></circle>`);
    }
    $$renderer2.push(`<!--]-->`);
    {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></svg></div>`);
    bind_props($$props, { data });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let history, totalPicks, totalHit, overallHitRate, bestDay, parlay3Wins, parlay5Wins, pnl, totalPnL, chartData, innerW, innerH, pnlSorted, pnlMin, pnlMax, pnlPoints, pnlPath, zeroY;
    let data = $$props["data"];
    const winAmount = 9.09;
    const loseAmount = 10;
    const W = 800;
    const H = 160;
    const PAD = { top: 15, right: 20, bottom: 35, left: 60 };
    function pnlX(i) {
      if (pnlSorted.length <= 1) return PAD.left + innerW / 2;
      return PAD.left + i / (pnlSorted.length - 1) * innerW;
    }
    function pnlY(val) {
      const range = pnlMax - pnlMin || 1;
      return PAD.top + innerH - (val - pnlMin) / range * innerH;
    }
    history = data.history;
    totalPicks = history.reduce((s, d) => s + d.picks_total, 0);
    totalHit = history.reduce((s, d) => s + d.picks_hit, 0);
    overallHitRate = totalPicks > 0 ? totalHit / totalPicks : 0;
    bestDay = history.length > 0 ? history.reduce((best, d) => d.hit_rate > best.hit_rate ? d : best) : null;
    history.length > 0 ? history.reduce((worst, d) => d.hit_rate < worst.hit_rate ? d : worst) : null;
    parlay3Wins = history.filter((d) => d.parlay_3_hit).length;
    parlay5Wins = history.filter((d) => d.parlay_5_hit).length;
    pnl = (() => {
      let running = 0;
      const points = [];
      const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
      for (const day of sorted) {
        const daily = day.picks_hit * winAmount - (day.picks_total - day.picks_hit) * loseAmount;
        running += daily;
        points.push({ date: day.date, cumulative: running, daily });
      }
      return points;
    })();
    totalPnL = pnl.length > 0 ? pnl[pnl.length - 1].cumulative : 0;
    chartData = history.map((d) => ({ date: d.date, hit_rate: d.hit_rate }));
    innerW = W - PAD.left - PAD.right;
    innerH = H - PAD.top - PAD.bottom;
    pnlSorted = [...pnl].sort((a, b) => a.date.localeCompare(b.date));
    pnlMin = pnlSorted.length > 0 ? Math.min(0, ...pnlSorted.map((p) => p.cumulative)) : -50;
    pnlMax = pnlSorted.length > 0 ? Math.max(0, ...pnlSorted.map((p) => p.cumulative)) : 50;
    pnlPoints = pnlSorted.map((p, i) => ({ x: pnlX(i), y: pnlY(p.cumulative), ...p }));
    pnlPath = (() => {
      if (pnlPoints.length === 0) return "";
      let d = `M ${pnlPoints[0].x} ${pnlPoints[0].y}`;
      for (let i = 1; i < pnlPoints.length; i++) {
        const prev = pnlPoints[i - 1];
        const curr = pnlPoints[i];
        const cpx = (prev.x + curr.x) / 2;
        d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
      }
      return d;
    })();
    zeroY = pnlY(0);
    head("1xl2tfr", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>ParlayBud — History</title>`);
      });
    });
    $$renderer2.push(`<div class="page svelte-1xl2tfr"><div class="container"><div class="page-title-row svelte-1xl2tfr"><div><h1 class="page-title svelte-1xl2tfr">Performance History</h1> <p class="page-subtitle svelte-1xl2tfr">Track record across all analyzed games</p></div></div> `);
    if (history.length === 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="empty-state glass svelte-1xl2tfr"><div class="empty-icon svelte-1xl2tfr">📅</div> <h2>No Historical Data</h2> <p>Results will appear here once picks have been graded.</p></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="summary-grid svelte-1xl2tfr"><div class="summary-card glass primary-card svelte-1xl2tfr"><div class="summary-label svelte-1xl2tfr">Overall Hit Rate</div> <div class="summary-big svelte-1xl2tfr"${attr_style(`color: ${stringify(overallHitRate >= 0.7 ? "#22c55e" : overallHitRate >= 0.6 ? "#f59e0b" : "#ef4444")};`)}>${escape_html((overallHitRate * 100).toFixed(1))}%</div> <div class="summary-detail svelte-1xl2tfr">${escape_html(totalHit)} / ${escape_html(totalPicks)} picks hit</div> <div class="hit-bar svelte-1xl2tfr"><div class="hit-fill svelte-1xl2tfr"${attr_style(`width: ${stringify(overallHitRate * 100)}%; background: ${stringify(overallHitRate >= 0.7 ? "#22c55e" : "#f59e0b")};`)}></div></div></div> <div class="summary-card glass svelte-1xl2tfr"><div class="summary-label svelte-1xl2tfr">Days Tracked</div> <div class="summary-big svelte-1xl2tfr">${escape_html(history.length)}</div> <div class="summary-detail svelte-1xl2tfr">${escape_html(totalPicks)} total picks analyzed</div></div> <div class="summary-card glass svelte-1xl2tfr"><div class="summary-label svelte-1xl2tfr">Best Day</div> `);
      if (bestDay) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="summary-big svelte-1xl2tfr" style="color: #22c55e;">${escape_html((bestDay.hit_rate * 100).toFixed(0))}%</div> <div class="summary-detail svelte-1xl2tfr">${escape_html(formatDateShort(bestDay.date))} • ${escape_html(bestDay.picks_hit)}/${escape_html(bestDay.picks_total)} picks</div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
        $$renderer2.push(`<div class="summary-big svelte-1xl2tfr">—</div>`);
      }
      $$renderer2.push(`<!--]--></div> <div class="summary-card glass svelte-1xl2tfr"><div class="summary-label svelte-1xl2tfr">Parlay Record</div> <div class="summary-row svelte-1xl2tfr"><div class="parlay-stat svelte-1xl2tfr"><span class="parlay-n svelte-1xl2tfr">3-Leg</span> <span class="parlay-record svelte-1xl2tfr" style="color: #22c55e;">${escape_html(parlay3Wins)}/${escape_html(history.length)}</span></div> <div class="parlay-divider svelte-1xl2tfr"></div> <div class="parlay-stat svelte-1xl2tfr"><span class="parlay-n svelte-1xl2tfr">5-Leg</span> <span class="parlay-record svelte-1xl2tfr" style="color: #f59e0b;">${escape_html(parlay5Wins)}/${escape_html(history.length)}</span></div></div></div> <div${attr_class("summary-card glass svelte-1xl2tfr", void 0, { "positive": totalPnL >= 0, "negative": totalPnL < 0 })}><div class="summary-label svelte-1xl2tfr">P&amp;L ($10/pick)</div> <div class="summary-big svelte-1xl2tfr"${attr_style(`color: ${stringify(totalPnL >= 0 ? "#22c55e" : "#ef4444")};`)}>${escape_html(totalPnL >= 0 ? "+" : "")}${escape_html(totalPnL.toFixed(2))}</div> <div class="summary-detail svelte-1xl2tfr">Flat betting simulation</div></div></div> <div class="chart-card glass svelte-1xl2tfr"><div class="chart-card-header svelte-1xl2tfr"><h2 class="chart-title svelte-1xl2tfr">Daily Hit Rate</h2> <div class="chart-legend svelte-1xl2tfr"><span class="legend-item svelte-1xl2tfr"><span class="legend-dot svelte-1xl2tfr" style="background: #f59e0b;"></span> 70% target</span> <span class="legend-item svelte-1xl2tfr"><span class="legend-dot svelte-1xl2tfr" style="background: #3b82f6;"></span> Actual rate</span></div></div> `);
      HitRateChart($$renderer2, { data: chartData });
      $$renderer2.push(`<!----></div> <div class="chart-card glass svelte-1xl2tfr"><div class="chart-card-header svelte-1xl2tfr"><h2 class="chart-title svelte-1xl2tfr">Cumulative P&amp;L</h2> <span class="pnl-total svelte-1xl2tfr"${attr_style(`color: ${stringify(totalPnL >= 0 ? "#22c55e" : "#ef4444")};`)}>${escape_html(totalPnL >= 0 ? "+" : "")}$${escape_html(totalPnL.toFixed(2))}</span></div> <div class="pnl-chart-wrap svelte-1xl2tfr"><svg${attr("viewBox", `0 0 ${stringify(W)} ${stringify(H)}`)} preserveAspectRatio="xMidYMid meet" class="pnl-svg svelte-1xl2tfr"><defs><linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%"${attr("stop-color", totalPnL >= 0 ? "#22c55e" : "#ef4444")} stop-opacity="0.2"></stop><stop offset="100%"${attr("stop-color", totalPnL >= 0 ? "#22c55e" : "#ef4444")} stop-opacity="0"></stop></linearGradient></defs><line${attr("x1", PAD.left)}${attr("y1", zeroY)}${attr("x2", PAD.left + innerW)}${attr("y2", zeroY)} stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="4 4"></line><text${attr("x", PAD.left - 6)}${attr("y", zeroY + 4)} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">$0</text><text${attr("x", PAD.left - 6)}${attr("y", PAD.top + 10)} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">$${escape_html(pnlMax.toFixed(0))}</text>`);
      if (pnlMin < 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<text${attr("x", PAD.left - 6)}${attr("y", PAD.top + innerH)} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">-$${escape_html(Math.abs(pnlMin).toFixed(0))}</text>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]-->`);
      if (pnlPoints.length > 1) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<path${attr("d", `${stringify(pnlPath)} L ${stringify(pnlPoints[pnlPoints.length - 1].x)} ${stringify(zeroY)} L ${stringify(pnlPoints[0].x)} ${stringify(zeroY)} Z`)} fill="url(#pnlGrad)"></path><path${attr("d", pnlPath)} fill="none"${attr("stroke", totalPnL >= 0 ? "#22c55e" : "#ef4444")} stroke-width="2.5" stroke-linecap="round"></path>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--><!--[-->`);
      const each_array = ensure_array_like(pnlPoints);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let pt = each_array[$$index];
        $$renderer2.push(`<circle${attr("cx", pt.x)}${attr("cy", pt.y)} r="4"${attr("fill", pt.cumulative >= 0 ? "#22c55e" : "#ef4444")} stroke="#0f172a" stroke-width="2"></circle>`);
      }
      $$renderer2.push(`<!--]--><!--[-->`);
      const each_array_1 = ensure_array_like(pnlPoints);
      for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
        let pt = each_array_1[i];
        if (i === 0 || i === pnlPoints.length - 1) {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<text${attr("x", pt.x)}${attr("y", PAD.top + innerH + 20)} text-anchor="middle" fill="#475569" font-size="10" font-family="Inter">${escape_html(formatDateShort(pt.date))}</text>`);
        } else {
          $$renderer2.push("<!--[-1-->");
        }
        $$renderer2.push(`<!--]-->`);
      }
      $$renderer2.push(`<!--]--></svg></div></div> <div class="history-table-wrap glass svelte-1xl2tfr"><div class="history-table-header svelte-1xl2tfr"><h2 class="chart-title svelte-1xl2tfr">Day-by-Day Results</h2></div> <div class="table-scroll svelte-1xl2tfr"><table class="history-table svelte-1xl2tfr"><thead class="svelte-1xl2tfr"><tr class="svelte-1xl2tfr"><th class="svelte-1xl2tfr">Date</th><th class="svelte-1xl2tfr">Picks</th><th class="svelte-1xl2tfr">Hit</th><th class="svelte-1xl2tfr">Hit Rate</th><th class="svelte-1xl2tfr">3-Leg</th><th class="svelte-1xl2tfr">5-Leg</th><th class="svelte-1xl2tfr">Daily P&amp;L</th></tr></thead><tbody><!--[-->`);
      const each_array_2 = ensure_array_like(history);
      for (let i = 0, $$length = each_array_2.length; i < $$length; i++) {
        let day = each_array_2[i];
        const dailyPnl = pnl.find((p) => p.date === day.date);
        $$renderer2.push(`<tr class="h-row svelte-1xl2tfr"${attr_style(`animation-delay: ${stringify(i * 40)}ms;`)}><td class="date-cell svelte-1xl2tfr">${escape_html(formatDateShort(day.date))}</td><td class="numeric-cell svelte-1xl2tfr">${escape_html(day.picks_total)}</td><td class="numeric-cell svelte-1xl2tfr">${escape_html(day.picks_hit)}</td><td class="numeric-cell svelte-1xl2tfr"><span class="rate-badge svelte-1xl2tfr"${attr_style(`color: ${stringify(day.hit_rate >= 0.7 ? "#22c55e" : day.hit_rate >= 0.6 ? "#f59e0b" : "#ef4444")}; background: ${stringify(day.hit_rate >= 0.7 ? "rgba(34,197,94,0.12)" : day.hit_rate >= 0.6 ? "rgba(245,158,11,0.12)" : "rgba(239,68,68,0.12)")};`)}>${escape_html((day.hit_rate * 100).toFixed(1))}%</span></td><td class="center-cell svelte-1xl2tfr"><span class="result-icon svelte-1xl2tfr">${escape_html(day.parlay_3_hit ? "✅" : "❌")}</span></td><td class="center-cell svelte-1xl2tfr"><span class="result-icon svelte-1xl2tfr">${escape_html(day.parlay_5_hit ? "✅" : "❌")}</span></td><td class="numeric-cell svelte-1xl2tfr">`);
        if (dailyPnl) {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<span${attr_style(`color: ${stringify(dailyPnl.daily >= 0 ? "#22c55e" : "#ef4444")}; font-weight: 700;`)}>${escape_html(dailyPnl.daily >= 0 ? "+" : "")}$${escape_html(dailyPnl.daily.toFixed(2))}</span>`);
        } else {
          $$renderer2.push("<!--[-1-->");
          $$renderer2.push(`—`);
        }
        $$renderer2.push(`<!--]--></td></tr>`);
      }
      $$renderer2.push(`<!--]--></tbody></table></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    bind_props($$props, { data });
  });
}
export {
  _page as default
};

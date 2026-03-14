import { ac as fallback, b as attr, ad as attr_style, c as escape_html, ae as bind_props, af as stringify, a as attr_class, e as ensure_array_like, ag as head } from "../../chunks/index2.js";
import { g as getProbabilityTier, a as getEdgeColor, b as getTeamColor, c as getStatColor, d as getTeamLogoUrl, f as formatOdds, e as formatPct, h as formatDateShort, i as formatDate } from "../../chunks/utils2.js";
function ProbabilityRing($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let tier, pct, radius, circumference, dashoffset, color;
    let prob = $$props["prob"];
    let size = fallback($$props["size"], 80);
    tier = getProbabilityTier(prob);
    pct = Math.round(prob * 100);
    radius = (size - 10) / 2;
    circumference = 2 * Math.PI * radius;
    dashoffset = circumference * (1 - prob);
    color = tier.color;
    $$renderer2.push(`<div class="ring-wrapper svelte-7gfy01"><svg${attr("width", size)}${attr("height", size)}${attr("viewBox", `0 0 ${stringify(size)} ${stringify(size)}`)}><circle${attr("cx", size / 2)}${attr("cy", size / 2)}${attr("r", radius)} fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"></circle><circle${attr("cx", size / 2)}${attr("cy", size / 2)}${attr("r", radius)} fill="none"${attr("stroke", color)} stroke-width="6" stroke-linecap="round"${attr("stroke-dasharray", circumference)}${attr("stroke-dashoffset", dashoffset)}${attr("transform", `rotate(-90 ${stringify(size / 2)} ${stringify(size / 2)})`)}${attr_style(`filter: drop-shadow(0 0 6px ${stringify(color)}80); transition: stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1);`)}></circle><text${attr("x", size / 2)}${attr("y", size / 2 + 1)} text-anchor="middle" dominant-baseline="middle"${attr("fill", color)} font-family="'Orbitron', sans-serif" font-weight="700"${attr("font-size", size * 0.2)}>${escape_html(pct)}%</text></svg> <span class="tier-label svelte-7gfy01"${attr_style(`color: ${stringify(color)}`)}>${escape_html(tier.label)}</span></div>`);
    bind_props($$props, { prob, size });
  });
}
function EdgeBadge($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let color, pct;
    let edge = $$props["edge"];
    color = getEdgeColor(edge);
    pct = (edge * 100).toFixed(1);
    $$renderer2.push(`<div class="edge-badge svelte-rmvgf8"${attr_style(`color: ${stringify(color)}; border-color: ${stringify(color)}40; background: ${stringify(color)}15;`)}><span class="edge-arrow svelte-rmvgf8">▲</span> <span class="edge-value svelte-rmvgf8">+${escape_html(pct)}% edge</span></div>`);
    bind_props($$props, { edge });
  });
}
function PickCard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let hitRate, teamColor, statColor, logoUrl, maxVal, bars;
    let pick = $$props["pick"];
    let isLock = fallback($$props["isLock"], false);
    let history = fallback($$props["history"], void 0);
    hitRate = history && history.attempts > 0 ? history.hits / history.attempts : null;
    teamColor = getTeamColor(pick.team);
    statColor = getStatColor(pick.stat);
    logoUrl = getTeamLogoUrl(pick.team);
    maxVal = Math.max(pick.season_avg, pick.last_5_avg, pick.last_3_avg, pick.line) * 1.15;
    bars = [
      { label: "Szn", value: pick.season_avg, color: "#94a3b8" },
      { label: "L5", value: pick.last_5_avg, color: "#60a5fa" },
      { label: "L3", value: pick.last_3_avg, color: "#34d399" }
    ];
    $$renderer2.push(`<div${attr_class("pick-card glass svelte-1caypvp", void 0, { "is-lock": isLock })}${attr_style(`border-left-color: ${stringify(teamColor)};`)}>`);
    if (isLock) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="lock-ribbon svelte-1caypvp">🔒 LOCK</div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (pick.has_live_line) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="live-badge svelte-1caypvp"><span class="live-dot svelte-1caypvp"></span> LIVE</div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> <div class="card-header svelte-1caypvp"><div class="player-info svelte-1caypvp"><div class="team-logo-wrap svelte-1caypvp"${attr_style(`background: ${stringify(teamColor)}20; border-color: ${stringify(teamColor)}40;`)}><img${attr("src", logoUrl)}${attr("alt", pick.team)} class="team-logo svelte-1caypvp"/></div> <div class="player-details svelte-1caypvp"><h3 class="player-name svelte-1caypvp">${escape_html(pick.player)}</h3> <div class="meta-row svelte-1caypvp"><span class="team-badge svelte-1caypvp"${attr_style(`background: ${stringify(teamColor)}25; color: ${stringify(teamColor)}; border-color: ${stringify(teamColor)}40;`)}>${escape_html(pick.team)}</span> <span class="vs-text svelte-1caypvp">vs ${escape_html(pick.opponent)}</span> <span class="location svelte-1caypvp">${escape_html(pick.is_home ? "🏠 Home" : "✈️ Away")}</span></div></div></div> <div class="prob-section svelte-1caypvp">`);
    ProbabilityRing($$renderer2, { prob: pick.model_prob, size: 88 });
    $$renderer2.push(`<!----></div></div> <div class="card-body svelte-1caypvp"><div class="bet-line svelte-1caypvp"><div class="stat-info svelte-1caypvp"><span class="stat-badge-styled svelte-1caypvp"${attr_style(`background: ${stringify(statColor)}20; color: ${stringify(statColor)}; border-color: ${stringify(statColor)}40;`)}>${escape_html(pick.stat)}</span> <span class="line-value svelte-1caypvp">O ${escape_html(pick.line)}</span> <span class="odds-value svelte-1caypvp">${escape_html(formatOdds(pick.over_odds))}</span></div> <div class="book-info svelte-1caypvp"><span class="book-label svelte-1caypvp">${escape_html(pick.book)}</span></div></div> <div class="mini-chart svelte-1caypvp"><div class="chart-bars svelte-1caypvp"><!--[-->`);
    const each_array = ensure_array_like(bars);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let bar = each_array[$$index];
      $$renderer2.push(`<div class="bar-item svelte-1caypvp"><div class="bar-track svelte-1caypvp"><div class="bar-fill svelte-1caypvp"${attr_style(`width: ${stringify(bar.value / maxVal * 100)}%; background: ${stringify(bar.color)};`)}></div> <div class="line-marker svelte-1caypvp"${attr_style(`left: ${stringify(pick.line / maxVal * 100)}%;`)}></div></div> <div class="bar-label-row svelte-1caypvp"><span class="bar-label svelte-1caypvp">${escape_html(bar.label)}</span> <span class="bar-value svelte-1caypvp"${attr_style(`color: ${stringify(bar.color)};`)}>${escape_html(bar.value.toFixed(1))}</span></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="line-legend svelte-1caypvp"><span class="line-dash svelte-1caypvp"></span> <span class="line-text svelte-1caypvp">Line: ${escape_html(pick.line)}</span></div></div> <div class="card-footer svelte-1caypvp">`);
    EdgeBadge($$renderer2, { edge: pick.edge });
    $$renderer2.push(`<!----> <div class="ev-value svelte-1caypvp">EV: <span style="color: #22c55e;" class="svelte-1caypvp">+${escape_html((pick.ev * 100).toFixed(1))}%</span></div></div> `);
    if (history && history.attempts > 0) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="past-record svelte-1caypvp"><div class="past-header svelte-1caypvp"><span class="past-label svelte-1caypvp">Past ${escape_html(history.attempts)}</span> <span class="past-rate svelte-1caypvp"${attr_style(`color: ${stringify(hitRate !== null && hitRate >= 0.7 ? "#22c55e" : hitRate !== null && hitRate >= 0.55 ? "#f59e0b" : "#ef4444")};`)}>${escape_html(history.hits)}/${escape_html(history.attempts)} <span class="past-pct svelte-1caypvp">(${escape_html(hitRate !== null ? (hitRate * 100).toFixed(0) : 0)}%)</span></span></div> <div class="dot-row svelte-1caypvp"><!--[-->`);
      const each_array_1 = ensure_array_like(history.recent);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let hit = each_array_1[$$index_1];
        $$renderer2.push(`<span${attr_class("result-dot svelte-1caypvp", void 0, { "dot-hit": hit, "dot-miss": !hit })}></span>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (history.attempts === 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="no-history svelte-1caypvp">No previous data</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div></div>`);
    } else if (history !== void 0) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<div class="past-record past-record--empty svelte-1caypvp"><span class="past-label svelte-1caypvp">No previous data for this prop</span></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div></div>`);
    bind_props($$props, { pick, isLock, history });
  });
}
function ParlayCard($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let is3Leg, accentColor, n, payoutMultiplier, combinedPct;
    let parlay = $$props["parlay"];
    let type = $$props["type"];
    let picks = $$props["picks"];
    function getPickForPlayer(playerName) {
      return picks.find((p) => p.player === playerName);
    }
    is3Leg = type === "3-Leg Safe";
    accentColor = is3Leg ? "#22c55e" : "#f59e0b";
    n = parlay.legs.length;
    payoutMultiplier = Math.pow(1.909, n);
    combinedPct = Math.round(parlay.combined_prob * 100);
    $$renderer2.push(`<div class="parlay-card glass svelte-td927n"${attr_style(`border-color: ${stringify(accentColor)}20; --accent: ${stringify(accentColor)};`)}><div class="parlay-header svelte-td927n"${attr_style(`border-bottom-color: ${stringify(accentColor)}20;`)}><div class="type-section svelte-td927n"><span class="type-icon svelte-td927n">${escape_html(is3Leg ? "🛡️" : "💎")}</span> <div class="type-info svelte-td927n"><span class="type-label svelte-td927n">${escape_html(type)}</span> <span class="type-sub svelte-td927n">${escape_html(n)} Leg Parlay</span></div></div> <div class="prob-pill svelte-td927n"${attr_style(`background: ${stringify(accentColor)}15; border-color: ${stringify(accentColor)}30; color: ${stringify(accentColor)};`)}><span class="prob-pct svelte-td927n">${escape_html(combinedPct)}%</span> <span class="prob-label svelte-td927n">Combined</span></div></div> <div class="legs-container svelte-td927n"><!--[-->`);
    const each_array = ensure_array_like(parlay.legs);
    for (let i = 0, $$length = each_array.length; i < $$length; i++) {
      let leg = each_array[i];
      const playerPick = getPickForPlayer(parlay.players[i]);
      $$renderer2.push(`<div class="leg-item svelte-td927n"><div class="leg-connector svelte-td927n"><div class="leg-dot svelte-td927n"${attr_style(`background: ${stringify(accentColor)}; box-shadow: 0 0 8px ${stringify(accentColor)}60;`)}></div> `);
      if (i < parlay.legs.length - 1) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="leg-line svelte-td927n"${attr_style(`background: linear-gradient(to bottom, ${stringify(accentColor)}40, ${stringify(accentColor)}10);`)}></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div> <div class="leg-content svelte-td927n"><div class="leg-player svelte-td927n">${escape_html(parlay.players[i])}</div> <div class="leg-detail svelte-td927n">`);
      if (playerPick) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="leg-stat-badge svelte-td927n"${attr_style(`background: ${stringify(getStatColor(playerPick.stat))}20; color: ${stringify(getStatColor(playerPick.stat))}; border-color: ${stringify(getStatColor(playerPick.stat))}30;`)}>${escape_html(playerPick.stat)}</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> <span class="leg-line-text svelte-td927n">${escape_html(leg.split(" ").slice(-2).join(" "))}</span> `);
      if (playerPick) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="leg-prob svelte-td927n"${attr_style(`color: ${stringify(accentColor)};`)}>${escape_html(Math.round(playerPick.model_prob * 100))}%</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div></div></div>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="parlay-footer svelte-td927n"${attr_style(`border-top-color: ${stringify(accentColor)}20;`)}><div class="payout-info svelte-td927n"><span class="payout-label svelte-td927n">Est. Payout</span> <span class="payout-multiplier svelte-td927n"${attr_style(`color: ${stringify(accentColor)};`)}>${escape_html(payoutMultiplier.toFixed(1))}x</span></div> <div class="parlay-note svelte-td927n"><span class="note-text">$10 → <strong${attr_style(`color: ${stringify(accentColor)};`)}>$${escape_html((10 * payoutMultiplier).toFixed(2))}</strong></span></div></div></div>`);
    bind_props($$props, { parlay, type, picks });
  });
}
function InjuriesList($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let injuries = $$props["injuries"];
    let collapsed = false;
    function getStatusColor(status) {
      if (status === "OUT") return "#ef4444";
      if (status === "QUESTIONABLE") return "#f59e0b";
      if (status === "PROBABLE") return "#22c55e";
      return "#94a3b8";
    }
    function getStatusBg(status) {
      if (status === "OUT") return "rgba(239,68,68,0.12)";
      if (status === "QUESTIONABLE") return "rgba(245,158,11,0.12)";
      if (status === "PROBABLE") return "rgba(34,197,94,0.12)";
      return "rgba(148,163,184,0.12)";
    }
    $$renderer2.push(`<div class="injuries-widget glass svelte-12mtdcx"><button class="injuries-header svelte-12mtdcx"><div class="header-left svelte-12mtdcx"><span class="header-icon svelte-12mtdcx">🚨</span> <span class="header-title svelte-12mtdcx">Injury Report</span> <span class="injuries-count svelte-12mtdcx">${escape_html(injuries.length)}</span></div> <span${attr_class("collapse-icon svelte-12mtdcx", void 0, { "rotated": collapsed })}>▼</span></button> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="injuries-list svelte-12mtdcx"><!--[-->`);
      const each_array = ensure_array_like(injuries);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let injury = each_array[$$index];
        const color = getStatusColor(injury.status);
        const bg = getStatusBg(injury.status);
        $$renderer2.push(`<div class="injury-item svelte-12mtdcx"><div class="injury-info svelte-12mtdcx"><span class="injury-player svelte-12mtdcx">${escape_html(injury.player)}</span> <span class="injury-reason svelte-12mtdcx">${escape_html(injury.reason)}</span></div> <span class="status-badge svelte-12mtdcx"${attr_style(`color: ${stringify(color)}; background: ${stringify(bg)}; border-color: ${stringify(color)}30;`)}>${escape_html(injury.status)}</span></div>`);
      }
      $$renderer2.push(`<!--]--> `);
      if (injuries.length === 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="no-injuries svelte-12mtdcx"><span>✅ No significant injuries</span></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { injuries });
  });
}
function PicksTable($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let filtered, sorted;
    let picks = $$props["picks"];
    let sortKey = "model_prob";
    let sortDir = -1;
    let activeFilter = "All";
    function getSortIcon(key) {
      if (sortKey !== key) return "↕";
      return "↓";
    }
    function getProbColor(prob) {
      if (prob >= 0.72) return "#22c55e";
      if (prob >= 0.65) return "#86efac";
      if (prob >= 0.6) return "#f59e0b";
      return "#94a3b8";
    }
    filtered = picks;
    sorted = [...filtered].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * sortDir;
      return String(av).localeCompare(String(bv)) * sortDir;
    });
    $$renderer2.push(`<div class="table-wrapper svelte-kdmj8a"><div class="table-controls svelte-kdmj8a"><div class="filter-tabs svelte-kdmj8a"><!--[-->`);
    const each_array = ensure_array_like(["All", "PTS", "REB", "AST"]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let filter = each_array[$$index];
      $$renderer2.push(`<button${attr_class("filter-tab svelte-kdmj8a", void 0, { "active": activeFilter === filter })}${attr_style(activeFilter === filter && filter !== "All" ? `color: ${getStatColor(filter)}; border-color: ${getStatColor(filter)}40; background: ${getStatColor(filter)}10;` : "")}>${escape_html(filter)} `);
      if (filter !== "All") {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<span class="tab-count svelte-kdmj8a">${escape_html(picks.filter((p) => p.stat === filter).length)}</span>`);
      } else {
        $$renderer2.push("<!--[-1-->");
        $$renderer2.push(`<span class="tab-count svelte-kdmj8a">${escape_html(picks.length)}</span>`);
      }
      $$renderer2.push(`<!--]--></button>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="table-meta svelte-kdmj8a"><span class="meta-text">${escape_html(sorted.length)} picks</span></div></div> <div class="table-scroll svelte-kdmj8a"><table class="picks-table svelte-kdmj8a"><thead class="svelte-kdmj8a"><tr class="svelte-kdmj8a"><th class="sortable svelte-kdmj8a">Player <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("player"))}</span></th><th class="sortable svelte-kdmj8a">Team <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("team"))}</span></th><th class="sortable svelte-kdmj8a">Stat <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("stat"))}</span></th><th class="sortable svelte-kdmj8a">Line <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("line"))}</span></th><th class="sortable svelte-kdmj8a">P(Over) <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("model_prob"))}</span></th><th class="sortable svelte-kdmj8a">Edge <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("edge"))}</span></th><th class="sortable svelte-kdmj8a">EV <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("ev"))}</span></th><th class="sortable svelte-kdmj8a">Szn Avg <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("season_avg"))}</span></th><th class="sortable svelte-kdmj8a">L5 <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("last_5_avg"))}</span></th><th class="sortable svelte-kdmj8a">L3 <span class="sort-icon svelte-kdmj8a">${escape_html(getSortIcon("last_3_avg"))}</span></th><th class="svelte-kdmj8a">Opp</th><th class="svelte-kdmj8a">Book</th></tr></thead><tbody><!--[-->`);
    const each_array_1 = ensure_array_like(sorted);
    for (let i = 0, $$length = each_array_1.length; i < $$length; i++) {
      let pick = each_array_1[i];
      const probColor = getProbColor(pick.model_prob);
      const edgeColor = getEdgeColor(pick.edge);
      const statColor = getStatColor(pick.stat);
      $$renderer2.push(`<tr class="table-row svelte-kdmj8a"${attr_style(`animation-delay: ${stringify(i * 30)}ms`)}><td class="player-cell svelte-kdmj8a"><span class="player-name svelte-kdmj8a">${escape_html(pick.player)}</span></td><td class="svelte-kdmj8a"><span class="team-chip svelte-kdmj8a"${attr_style(`color: ${stringify(statColor)}; border-color: ${stringify(statColor)}20; background: ${stringify(statColor)}10;`)}>${escape_html(pick.team)}</span></td><td class="svelte-kdmj8a"><span class="stat-chip svelte-kdmj8a"${attr_style(`color: ${stringify(statColor)}; background: ${stringify(statColor)}15; border-color: ${stringify(statColor)}30;`)}>${escape_html(pick.stat)}</span></td><td class="numeric svelte-kdmj8a"><span class="line-val svelte-kdmj8a">O ${escape_html(pick.line)}</span> <span class="odds-val svelte-kdmj8a">${escape_html(formatOdds(pick.over_odds))}</span></td><td class="numeric svelte-kdmj8a"><span class="prob-val svelte-kdmj8a"${attr_style(`color: ${stringify(probColor)};`)}>${escape_html(formatPct(pick.model_prob))}</span></td><td class="numeric svelte-kdmj8a"><span class="edge-val svelte-kdmj8a"${attr_style(`color: ${stringify(edgeColor)};`)}>+${escape_html(formatPct(pick.edge))}</span></td><td class="numeric svelte-kdmj8a"><span class="ev-val svelte-kdmj8a" style="color: #22c55e;">+${escape_html((pick.ev * 100).toFixed(1))}%</span></td><td class="numeric svelte-kdmj8a">${escape_html(pick.season_avg.toFixed(1))}</td><td class="numeric svelte-kdmj8a">${escape_html(pick.last_5_avg.toFixed(1))}</td><td class="numeric svelte-kdmj8a">${escape_html(pick.last_3_avg.toFixed(1))}</td><td class="opp-cell svelte-kdmj8a">${escape_html(pick.opponent)}</td><td class="book-cell svelte-kdmj8a"><span class="book-badge svelte-kdmj8a">${escape_html(pick.book)}</span></td></tr>`);
    }
    $$renderer2.push(`<!--]--></tbody></table></div></div>`);
    bind_props($$props, { picks });
  });
}
function DateNav($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let isToday, isFuture, hasNext, prevHasData, nextHasData;
    let date = $$props["date"];
    let today = $$props["today"];
    let prevDate = $$props["prevDate"];
    let nextDate = $$props["nextDate"];
    let availableDates = fallback($$props["availableDates"], () => [], true);
    isToday = date === today;
    isFuture = date >= today;
    hasNext = !isFuture;
    prevHasData = availableDates.includes(prevDate);
    nextHasData = availableDates.includes(nextDate);
    $$renderer2.push(`<div class="date-nav glass svelte-r9vtch"><a${attr("href", `/?date=${stringify(prevDate)}`)}${attr_class("nav-btn svelte-r9vtch", void 0, { "faded": !prevHasData })} aria-label="Previous day">‹</a> <div class="date-center svelte-r9vtch"><div class="date-display svelte-r9vtch"><span class="date-formatted svelte-r9vtch">${escape_html(formatDateShort(date))}</span> `);
    if (isToday) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<span class="today-chip svelte-r9vtch">Today</span>`);
    } else if (isFuture) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<span class="future-chip svelte-r9vtch">Future</span>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div> `);
    if (!isToday) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<a href="/" class="back-today svelte-r9vtch">↩ Back to today</a>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></div> <a${attr("href", hasNext ? `/?date=${nextDate}` : null)}${attr_class("nav-btn svelte-r9vtch", void 0, { "disabled": !hasNext, "faded": hasNext && !nextHasData })} aria-label="Next day"${attr("aria-disabled", !hasNext)}>›</a></div>`);
    bind_props($$props, { date, today, prevDate, nextDate, availableDates });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let picks, isDemo, legHistory, lockPicks, otherPicks, avgProb, minProb, maxProb;
    let data = $$props["data"];
    function getHistory(player, stat) {
      return legHistory[`${player}|${stat}`];
    }
    picks = data.picks;
    isDemo = data.isDemo ?? false;
    legHistory = data.legHistory ?? {};
    lockPicks = picks ? picks.picks.filter((p) => picks.locks.includes(p.player)) : [];
    otherPicks = picks ? picks.picks.filter((p) => !picks.locks.includes(p.player)) : [];
    avgProb = picks ? picks.picks.reduce((s, p) => s + p.model_prob, 0) / picks.picks.length : 0;
    minProb = picks ? Math.min(...picks.picks.map((p) => p.model_prob)) : 0;
    maxProb = picks ? Math.max(...picks.picks.map((p) => p.model_prob)) : 0;
    head("1uha8ag", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>ParlayBud — Dashboard</title>`);
      });
    });
    $$renderer2.push(`<div class="page svelte-1uha8ag"><div class="container">`);
    DateNav($$renderer2, {
      date: data.date,
      today: data.today,
      prevDate: data.prevDate,
      nextDate: data.nextDate,
      availableDates: data.availableDates
    });
    $$renderer2.push(`<!----> `);
    if (!picks) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="empty-state glass svelte-1uha8ag"><div class="empty-icon svelte-1uha8ag">🏀</div> <h2 class="empty-title svelte-1uha8ag">No Picks Available</h2> <p class="empty-desc svelte-1uha8ag">${escape_html(data.date === data.today ? "Today's" : "No")} ML model picks ${escape_html(data.date === data.today ? "haven't been generated yet. Check back after 2 PM EST when game lines are posted." : `available for ${data.date}.`)}</p> <div class="empty-hint svelte-1uha8ag">Looking for: <code class="svelte-1uha8ag">/picks/${escape_html(data.date)}.json</code></div></div>`);
    } else {
      $$renderer2.push("<!--[-1-->");
      if (isDemo) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="demo-banner svelte-1uha8ag"><span class="demo-icon svelte-1uha8ag">⚡</span> <span>Showing demo data for <strong>${escape_html(picks.date)}</strong> — No picks found for today</span></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> <div class="page-header glass svelte-1uha8ag"><div class="header-main svelte-1uha8ag"><div class="header-date-section"><div class="header-badge svelte-1uha8ag"><span class="header-badge-dot svelte-1uha8ag"></span> ML PREDICTIONS</div> <h1 class="header-date svelte-1uha8ag">${escape_html(formatDate(picks.date))}</h1> <div class="header-meta svelte-1uha8ag"><span class="meta-chip svelte-1uha8ag"><span class="meta-icon svelte-1uha8ag">🤖</span> ${escape_html(picks.model_version)}</span> <span class="meta-chip svelte-1uha8ag"><span class="meta-icon svelte-1uha8ag">🕐</span> Generated ${escape_html(new Date(picks.generated_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }))}</span></div></div> <div class="header-games svelte-1uha8ag"><div class="games-label svelte-1uha8ag">Games Tonight</div> <div class="games-list svelte-1uha8ag"><!--[-->`);
      const each_array = ensure_array_like(picks.games);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let game = each_array[$$index];
        $$renderer2.push(`<div class="game-chip svelte-1uha8ag"><span class="game-away svelte-1uha8ag">${escape_html(game.away)}</span> <span class="game-at svelte-1uha8ag">@</span> <span class="game-home svelte-1uha8ag">${escape_html(game.home)}</span></div>`);
      }
      $$renderer2.push(`<!--]--></div></div></div></div> <div class="stats-bar svelte-1uha8ag"><div class="stat-card glass svelte-1uha8ag"><div class="stat-label svelte-1uha8ag">Today's Picks</div> <div class="stat-value svelte-1uha8ag">${escape_html(picks.picks.length)}</div> <div class="stat-sub svelte-1uha8ag">total selections</div></div> <div class="stat-card glass svelte-1uha8ag"><div class="stat-label svelte-1uha8ag">Avg Confidence</div> <div class="stat-value svelte-1uha8ag" style="color: #22c55e;">${escape_html((avgProb * 100).toFixed(1))}%</div> <div class="stat-sub svelte-1uha8ag">model probability</div></div> <div class="stat-card glass svelte-1uha8ag"><div class="stat-label svelte-1uha8ag">Confidence Range</div> <div class="stat-value svelte-1uha8ag" style="font-size: 1.2rem;">${escape_html((minProb * 100).toFixed(1))}–${escape_html((maxProb * 100).toFixed(1))}%</div> <div class="stat-sub svelte-1uha8ag">min to max</div></div> <div class="stat-card glass svelte-1uha8ag"><div class="stat-label svelte-1uha8ag">Locks Today</div> <div class="stat-value svelte-1uha8ag" style="color: #f59e0b;">🔒 ${escape_html(picks.locks.length)}</div> <div class="stat-sub svelte-1uha8ag">high confidence</div></div> <div class="stat-card glass svelte-1uha8ag"><div class="stat-label svelte-1uha8ag">Model AUC</div> <div class="stat-value svelte-1uha8ag" style="color: #3b82f6;">${escape_html(picks.model_stats.PTS.auc.toFixed(3))}</div> <div class="stat-sub svelte-1uha8ag">PTS model</div></div></div> <div class="two-col-layout svelte-1uha8ag"><div class="left-col svelte-1uha8ag"><section class="locks-section"><div class="section-header locks-header svelte-1uha8ag"><div class="section-title-group svelte-1uha8ag"><span class="section-icon locks-icon svelte-1uha8ag">🔒</span> <h2 class="section-title svelte-1uha8ag">Today's Locks</h2> <span class="lock-count-badge svelte-1uha8ag">${escape_html(lockPicks.length)}</span></div> <div class="locks-subtitle svelte-1uha8ag">Highest conviction picks</div></div> <div class="locks-grid svelte-1uha8ag"><!--[-->`);
      const each_array_1 = ensure_array_like(lockPicks);
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        let pick = each_array_1[$$index_1];
        PickCard($$renderer2, {
          pick,
          isLock: true,
          history: getHistory(pick.player, pick.stat)
        });
      }
      $$renderer2.push(`<!--]--></div></section> <section class="parlays-section"><div class="section-header svelte-1uha8ag"><div class="section-title-group svelte-1uha8ag"><span class="section-icon svelte-1uha8ag">🎯</span> <h2 class="section-title svelte-1uha8ag">Today's Parlays</h2></div></div> <div class="parlays-grid svelte-1uha8ag">`);
      ParlayCard($$renderer2, {
        parlay: picks.parlay_3leg,
        type: "3-Leg Safe",
        picks: picks.picks
      });
      $$renderer2.push(`<!----> `);
      ParlayCard($$renderer2, {
        parlay: picks.parlay_5leg,
        type: "5-Leg Premium",
        picks: picks.picks
      });
      $$renderer2.push(`<!----></div></section> <section class="all-picks-section"><div class="section-header svelte-1uha8ag"><div class="section-title-group svelte-1uha8ag"><span class="section-icon svelte-1uha8ag">📊</span> <h2 class="section-title svelte-1uha8ag">All Picks</h2></div></div> `);
      PicksTable($$renderer2, { picks: picks.picks });
      $$renderer2.push(`<!----></section> `);
      if (otherPicks.length > 0) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<section class="other-picks-section"><div class="section-header svelte-1uha8ag"><div class="section-title-group svelte-1uha8ag"><span class="section-icon svelte-1uha8ag">🎲</span> <h2 class="section-title svelte-1uha8ag">Additional Picks</h2> <span class="count-badge svelte-1uha8ag">${escape_html(otherPicks.length)}</span></div></div> <div class="other-picks-grid svelte-1uha8ag"><!--[-->`);
        const each_array_2 = ensure_array_like(otherPicks);
        for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
          let pick = each_array_2[$$index_2];
          PickCard($$renderer2, {
            pick,
            isLock: false,
            history: getHistory(pick.player, pick.stat)
          });
        }
        $$renderer2.push(`<!--]--></div></section>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div> <div class="right-col svelte-1uha8ag"><div class="sidebar-widget glass svelte-1uha8ag"><div class="widget-header svelte-1uha8ag"><span class="widget-icon svelte-1uha8ag">🏟️</span> <span class="widget-title svelte-1uha8ag">Games Tonight</span></div> <div class="games-widget-list svelte-1uha8ag"><!--[-->`);
      const each_array_3 = ensure_array_like(picks.games);
      for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
        let game = each_array_3[$$index_3];
        $$renderer2.push(`<div class="game-row svelte-1uha8ag"><div class="game-teams svelte-1uha8ag"><span class="game-team away svelte-1uha8ag">${escape_html(game.away)}</span> <span class="game-separator svelte-1uha8ag">@</span> <span class="game-team home svelte-1uha8ag">${escape_html(game.home)}</span></div> <span class="game-picks-count svelte-1uha8ag">${escape_html(picks.picks.filter((p) => p.game === game.label).length)} picks</span></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> <div class="sidebar-widget glass svelte-1uha8ag"><div class="widget-header svelte-1uha8ag"><span class="widget-icon svelte-1uha8ag">🧠</span> <span class="widget-title svelte-1uha8ag">Model Stats</span></div> <div class="model-stats-grid svelte-1uha8ag"><!--[-->`);
      const each_array_4 = ensure_array_like(Object.entries(picks.model_stats));
      for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
        let [stat, stats] = each_array_4[$$index_4];
        $$renderer2.push(`<div class="model-stat-row svelte-1uha8ag"><span${attr_class(`model-stat-label stat-${stringify(stat.toLowerCase())}`, "svelte-1uha8ag")}>${escape_html(stat)}</span> <div class="model-stat-values svelte-1uha8ag"><div class="model-kv svelte-1uha8ag"><span class="model-k svelte-1uha8ag">AUC</span> <span class="model-v svelte-1uha8ag">${escape_html(stats.auc.toFixed(3))}</span></div> <div class="model-kv svelte-1uha8ag"><span class="model-k svelte-1uha8ag">Hit@70</span> <span class="model-v svelte-1uha8ag" style="color: #22c55e;">${escape_html((stats.hit_rate_70 * 100).toFixed(1))}%</span></div></div></div>`);
      }
      $$renderer2.push(`<!--]--></div></div> `);
      InjuriesList($$renderer2, { injuries: picks.injuries });
      $$renderer2.push(`<!----></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    bind_props($$props, { data });
  });
}
export {
  _page as default
};

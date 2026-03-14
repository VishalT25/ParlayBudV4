import { g as getContext, a as attr_class, e as ensure_array_like, b as attr, s as store_get, c as escape_html, u as unsubscribe_stores, d as slot } from "../../chunks/index2.js";
import "clsx";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../chunks/root.js";
import "../../chunks/state.svelte.js";
const getStores = () => {
  const stores$1 = getContext("__svelte__");
  return {
    /** @type {typeof page} */
    page: {
      subscribe: stores$1.page.subscribe
    },
    /** @type {typeof navigating} */
    navigating: {
      subscribe: stores$1.navigating.subscribe
    },
    /** @type {typeof updated} */
    updated: stores$1.updated
  };
};
const page = {
  subscribe(fn) {
    const store = getStores().page;
    return store.subscribe(fn);
  }
};
function Navbar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let menuOpen = false;
    const links = [
      { href: "/", label: "Dashboard", icon: "📊" },
      { href: "/history", label: "History", icon: "📅" },
      { href: "/model", label: "Model", icon: "🧠" }
    ];
    $$renderer2.push(`<nav class="navbar svelte-rfuq4y"><div class="container nav-inner svelte-rfuq4y"><a href="/" class="logo svelte-rfuq4y"><span class="logo-icon svelte-rfuq4y">🏀</span> <span class="logo-text svelte-rfuq4y">ParlayBud</span> <span class="logo-version svelte-rfuq4y">V4</span></a> <div${attr_class("nav-links svelte-rfuq4y", void 0, { "open": menuOpen })}><!--[-->`);
    const each_array = ensure_array_like(links);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let link = each_array[$$index];
      $$renderer2.push(`<a${attr("href", link.href)}${attr_class("nav-link svelte-rfuq4y", void 0, {
        "active": store_get($$store_subs ??= {}, "$page", page).url.pathname === link.href
      })}><span class="nav-icon svelte-rfuq4y">${escape_html(link.icon)}</span> <span class="nav-label">${escape_html(link.label)}</span></a>`);
    }
    $$renderer2.push(`<!--]--></div> <button class="hamburger svelte-rfuq4y" aria-label="Menu"><span${attr_class("svelte-rfuq4y", void 0, { "open": menuOpen })}></span> <span${attr_class("svelte-rfuq4y", void 0, { "open": menuOpen })}></span> <span${attr_class("svelte-rfuq4y", void 0, { "open": menuOpen })}></span></button></div></nav>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function _layout($$renderer, $$props) {
  Navbar($$renderer);
  $$renderer.push(`<!----> <main class="main-content svelte-12qhfyh"><!--[-->`);
  slot($$renderer, $$props, "default", {});
  $$renderer.push(`<!--]--></main> <footer class="site-footer svelte-12qhfyh"><div class="container"><p class="disclaimer svelte-12qhfyh">⚠️ For entertainment purposes only. Not financial advice. Gambling involves risk.</p> <p class="footer-note svelte-12qhfyh">ParlayBud V4 • XGBoost ML Models • 34,763 game logs</p></div></footer>`);
}
export {
  _layout as default
};

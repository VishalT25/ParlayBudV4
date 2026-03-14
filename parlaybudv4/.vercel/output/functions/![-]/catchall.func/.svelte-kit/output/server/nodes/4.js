import * as universal from '../entries/pages/model/_page.ts.js';

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/model/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/model/+page.ts";
export const imports = ["_app/immutable/nodes/4.8cFCg5TK.js","_app/immutable/chunks/CrlIH5jG.js","_app/immutable/chunks/mxgC9ynA.js","_app/immutable/chunks/hk8jYNMC.js","_app/immutable/chunks/CXrMECyh.js","_app/immutable/chunks/BawvSKyM.js","_app/immutable/chunks/B5Ts1cDx.js","_app/immutable/chunks/C74CPKy6.js"];
export const stylesheets = ["_app/immutable/assets/4.CDfMLJXw.css"];
export const fonts = [];

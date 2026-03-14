import * as universal from '../entries/pages/_page.ts.js';

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/+page.ts";
export const imports = ["_app/immutable/nodes/2.DaFsbpKU.js","_app/immutable/chunks/CrlIH5jG.js","_app/immutable/chunks/mxgC9ynA.js","_app/immutable/chunks/hk8jYNMC.js","_app/immutable/chunks/CXrMECyh.js","_app/immutable/chunks/BawvSKyM.js","_app/immutable/chunks/B5Ts1cDx.js","_app/immutable/chunks/C74CPKy6.js"];
export const stylesheets = ["_app/immutable/assets/2.xLM0XquK.css"];
export const fonts = [];

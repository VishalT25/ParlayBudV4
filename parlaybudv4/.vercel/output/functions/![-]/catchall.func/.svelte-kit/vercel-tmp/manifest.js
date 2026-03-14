export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set(["metrics.json","picks/2026-03-11.json","picks/2026-03-12.json","picks/2026-03-13.json","picks/2026-03-14.json"]),
	mimeTypes: {".json":"application/json"},
	_: {
		client: {start:"_app/immutable/entry/start.Cczmp4GY.js",app:"_app/immutable/entry/app.D6Bt5ahr.js",imports:["_app/immutable/entry/start.Cczmp4GY.js","_app/immutable/chunks/KAczVnXl.js","_app/immutable/chunks/mxgC9ynA.js","_app/immutable/chunks/rgW7MAQh.js","_app/immutable/entry/app.D6Bt5ahr.js","_app/immutable/chunks/mxgC9ynA.js","_app/immutable/chunks/CrlIH5jG.js","_app/immutable/chunks/rgW7MAQh.js","_app/immutable/chunks/CXrMECyh.js","_app/immutable/chunks/BawvSKyM.js"],stylesheets:[],fonts:[],uses_env_dynamic_public:false},
		nodes: [
			__memo(() => import('../output/server/nodes/0.js')),
			__memo(() => import('../output/server/nodes/1.js')),
			__memo(() => import('../output/server/nodes/2.js')),
			__memo(() => import('../output/server/nodes/3.js')),
			__memo(() => import('../output/server/nodes/4.js'))
		],
		remotes: {
			
		},
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/api/picks/[date]",
				pattern: /^\/api\/picks\/([^/]+?)\/?$/,
				params: [{"name":"date","optional":false,"rest":false,"chained":false}],
				page: null,
				endpoint: __memo(() => import('../output/server/entries/endpoints/api/picks/_date_/_server.ts.js'))
			},
			{
				id: "/history",
				pattern: /^\/history\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			},
			{
				id: "/model",
				pattern: /^\/model\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			}
		],
		prerendered_routes: new Set([]),
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();

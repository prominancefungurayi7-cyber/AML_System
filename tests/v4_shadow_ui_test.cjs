'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const entries = [];
const state = {textContent: ''};
const list = {replaceChildren: () => { entries.length = 0; }, appendChild: x => entries.push(x)};
const rows = [
  {transaction_id:'9007199254740993',status:'success',decision:'normal',suspicious_probability:0.2},
  {transaction_id:'9007199254740994',status:'success',decision:'suspicious_pattern',suspicious_probability:0.5},
  {transaction_id:'9007199254740995',status:'inference_error',decision:'inference_error',suspicious_probability:null}
].map(r => Object.assign(r, {threshold:0.5,model_version:'v4.development.freeze.stage23.1',feature_version:'v4.features.1',inference_timestamp:'2026-10-06T00:00:00.000000Z'}));
let retried = false;
const posts = [];
const context = {
  URLSearchParams,
  crypto: {randomUUID: () => '11111111-1111-4111-8111-111111111111'},
  document: {getElementById: id => id==='v4-shadow-results' ? list : id==='v4-shadow-state' ? state : {}, createElement: () => ({textContent:'', children:[], appendChild(child){this.children.push(child);}})},
  window: {addEventListener: () => {}, confirm: () => true, showAmlNotification: () => {}},
  fetch: async (url, options={}) => {
    if (url.endsWith('/retry')) {
      posts.push(options); retried = true;
      return {ok:true,json:async () => ({status:'success'})};
    }
    if (url.startsWith('/compliance/v4-error/'))
      return {ok:true,json:async () => ({effective_ai_state:retried ? 'normal' : 'inference_error',csrf_token:'test-token',case_closed:false})};
    return {ok:true,json:async () => ({results:rows})};
  }
};
vm.runInNewContext(fs.readFileSync('static/v4-shadow.js','utf8'),context);
setImmediate(async () => {
  assert.strictEqual(entries.length,3);
  assert(entries[0].textContent.includes('9007199254740993: No suspicious pattern'));
  assert(entries[1].textContent.includes('requires analyst review'));
  assert(entries[1].textContent.includes('Suspicious probability: 0.5'));
  assert(entries[2].textContent.includes('V4 inference unavailable.'));
  assert(entries[2].textContent.includes('Suspicious probability: unavailable'));
  assert.strictEqual(entries[2].children[0].textContent, 'Review / Retry Analysis');
  for (const entry of entries) assert(entry.textContent.includes('Features: v4.features.1'));
  await entries[2].children[0].onclick();
  assert.strictEqual(posts.length,1);
  assert.strictEqual(posts[0].body.get('csrf_token'),'test-token');
  await entries[2].children[0].onclick();
  assert.strictEqual(posts.length,1);
  console.log('Three rendered shadow states and exact large IDs: PASS');
  await checkQueuedRefresh();
});

async function checkQueuedRefresh() {
  const filter = {value:'latest'};
  const nodes = [];
  const listeners = {};
  const emissions = [];
  const requests = [];
  let resolveInitial;
  const socket = {connected:true, on:(name,fn) => {listeners[name]=fn;},
    emit:(name) => emissions.push(name)};
  const sandbox = {
    document: {getElementById:id => id==='v4-result-filter' ? filter :
      id==='v4-shadow-state' ? {textContent:''} : id==='v4-shadow-results' ? {
        replaceChildren:()=>{nodes.length=0;},appendChild:node=>nodes.push(node)} : {},
      createElement:()=>({textContent:'',appendChild:()=>{}})},
    window:{io:()=>socket,getAmlSocket:()=>socket,addEventListener:()=>{}},
    fetch:async url=>{
      requests.push(url);
      if (requests.length===1) return await new Promise(resolve=>{resolveInitial=resolve;});
      return {ok:true,json:async()=>({results:[rows[2]]})};
    }
  };
  vm.runInNewContext(fs.readFileSync('static/v4-shadow.js','utf8'),sandbox);
  assert.deepStrictEqual(emissions,['v4_shadow_subscribe']);
  filter.value='errors';
  filter.onchange();
  listeners.v4_shadow_result();
  resolveInitial({ok:true,json:async()=>({results:rows})});
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepStrictEqual(requests,['/api/v4-shadow/results','/api/v4-shadow/results?errors=1']);
  assert.strictEqual(nodes.length,1);
  assert(nodes[0].textContent.includes('9007199254740995'));
  console.log('Connected subscription and queued filter/live refresh: PASS');
}

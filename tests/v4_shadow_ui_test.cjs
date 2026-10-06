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
const context = {
  document: {getElementById: id => id==='v4-shadow-results' ? list : id==='v4-shadow-state' ? state : {}, createElement: () => ({textContent:''})},
  window: {addEventListener: () => {}},
  fetch: async () => ({ok:true,json:async () => ({results:rows})})
};
vm.runInNewContext(fs.readFileSync('static/v4-shadow.js','utf8'),context);
setImmediate(() => {
  assert.strictEqual(entries.length,3);
  assert(entries[0].textContent.includes('9007199254740993: No suspicious pattern'));
  assert(entries[1].textContent.includes('requires analyst review'));
  assert(entries[1].textContent.includes('Suspicious probability: 0.5'));
  assert(entries[2].textContent.includes('V4 inference unavailable.'));
  assert(entries[2].textContent.includes('Suspicious probability: unavailable'));
  for (const entry of entries) assert(entry.textContent.includes('Features: v4.features.1'));
  console.log('Three rendered shadow states and exact large IDs: PASS');
});

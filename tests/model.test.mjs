import test from "node:test";
import assert from "node:assert/strict";
import {matching,summarize,age} from "../web/model.mjs";
const samples = [{col:7,taxon:2,name:"Old name",accepted:"Hylonomus"},{col:7,taxon:2,name:"Hylonomus sp.",accepted:"Hylonomus"},{col:8,taxon:0,name:"Undetermined",accepted:""}];
test("separate occurrences, collections and identified taxon IDs", () => {
  assert.deepEqual(summarize(samples,[7,8]),{collections:2,occurrences:3,taxa:1});
});
test("search includes identified and accepted names in the selected collection", () => {
  assert.equal(matching(samples,[7]," HYLONO ").length,2);
  assert.equal(matching(samples,[8],"Hylonomus").length,0);
});
test("age bounds retain full source width", () => assert.equal(age({old:318.7,young:316.9}),"318.7–316.9 Ma"));

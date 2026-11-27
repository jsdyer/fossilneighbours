import test from "node:test";
import assert from "node:assert/strict";
import {matching,summarize,age,containsAge,initialSelection} from "../web/model.mjs";
const samples = [{col:7,taxon:2,name:"Old name",accepted:"Hylonomus"},{col:7,taxon:2,name:"Hylonomus sp.",accepted:"Hylonomus"},{col:8,taxon:0,name:"Undetermined",accepted:""}];
test("separate occurrences, collections and identified taxon IDs", () => {
  assert.deepEqual(summarize(samples,[7,8]),{collections:2,occurrences:3,taxa:1});
});
test("search includes identified and accepted names in the selected collection", () => {
  assert.equal(matching(samples,[7]," HYLONO ").length,2);
  assert.equal(matching(samples,[8],"Hylonomus").length,0);
});
test("age bounds retain full source width", () => assert.equal(age({old:318.7,young:316.9}),"318.7–316.9 Ma"));

test("age searches include both endpoints and preserve an empty filter", () => {
  const collection = {old:10, young:9};
  for (const term of ["", "9", "9.5", "10"]) assert.ok(containsAge(collection,term));
  assert.equal(containsAge(collection,"11"),false);
});

test("validated record links restore additional formations and peers found only by the environment match", () => {
  const data = {presets:{Joggins:[3], Added:[8]}, collections:[
    {id:3, peers:{age:[2],environment:[]}}, {id:8,peers:{age:[1],environment:[7]}}]};
  const selection = initialSelection(data, new URLSearchParams("formation=Added&collection=8&peer=7"));
  assert.deepEqual(selection,{formation:"Added",collection:8,peer:7,environment:true,scope:"collection",identification:""});
  const unrelated = initialSelection(data,new URLSearchParams("formation=Added&collection=3&peer=2"));
  assert.equal(unrelated.collection,8);
  assert.equal(unrelated.peer,null);
});

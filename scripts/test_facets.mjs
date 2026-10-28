// Faceted job filters: OR within a facet, AND across facets, URL round-trip.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const app = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../site/assets/app.js"), "utf8");

function extract(source, name) {
  const start = source.indexOf("function " + name);
  if (start < 0) throw new Error("missing " + name);
  const brace = source.indexOf("{", start);
  let depth = 0;
  for (let i = brace; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") {
      depth--;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error("unclosed " + name);
}

const names = ["rjKeys", "rjFold", "rjBlank", "rjParseFacetQuery", "rjSerializeFacetQuery", "rjHave", "rjDays", "rjJobMatches", "rjFacetCounts"];
const ctx = {};
runInContext(names.map((name) => extract(app, name)).join("\n"), createContext(ctx));

const today = "2026-10-28";
const devops = {
  text: "Senior DevOps Engineer Kubernetes AWS",
  role: ["devops"], skill: ["kubernetes", "aws"], tz: ["eu-apac"], level: ["senior"],
  company: "acme", region: "vn", remote: "yes", group: "B", salary: "", posted: "2026-10-20", agg: 0,
};
const sre = {
  text: "Site Reliability Engineer AWS",
  role: ["sre"], skill: ["aws"], tz: ["us"], level: ["lead"],
  company: "beta", region: "global", remote: "yes", group: "A", salary: "yes", posted: "2026-09-01", agg: 0,
};
const backend = {
  text: "Backend Engineer",
  role: ["backend"], skill: [], tz: ["eu-apac"], level: [],
  company: "gamma", region: "apac", remote: "hybrid", group: "B", salary: "", posted: "", agg: 0,
};
const jobs = [devops, sre, backend];

assert.equal(ctx.rjJobMatches(devops, { role: ["devops", "sre"] }, today), true, "OR: devops matches role devops or sre");
assert.equal(ctx.rjJobMatches(sre, { role: ["devops", "sre"] }, today), true, "OR: sre matches role devops or sre");
assert.equal(ctx.rjJobMatches(backend, { role: ["devops", "sre"] }, today), false, "OR: backend matches neither devops nor sre");

const narrow = { role: ["devops"], skill: ["kubernetes"], tz: ["eu-apac"], level: ["senior"] };
assert.equal(ctx.rjJobMatches(devops, narrow, today), true, "AND: devops + kubernetes + eu-apac + senior");
assert.equal(ctx.rjJobMatches(sre, narrow, today), false, "AND: sre fails the devops facet");
assert.equal(ctx.rjJobMatches(devops, { role: ["devops"], skill: ["python"] }, today), false, "AND: missing skill rejects the job");
assert.equal(ctx.rjJobMatches(devops, { q: "kubernetes", role: ["devops"] }, today), true, "search AND facet");
assert.equal(ctx.rjJobMatches(devops, { q: "python", role: ["devops"] }, today), false, "search that misses the text rejects");
assert.equal(ctx.rjJobMatches({ text: "Việc làm DevOps", role: [], skill: [], tz: [], level: [], company: "a", region: "vn", remote: "yes", group: "A", salary: "", posted: "", agg: 0 }, { q: "viec" }, today), true, "search folds Vietnamese diacritics");

const agg = { text: "DevOps", role: ["devops"], skill: [], tz: ["eu-apac"], level: [], company: "huzzle", region: "global", remote: "yes", group: "B", salary: "", posted: "", agg: 1 };
assert.equal(ctx.rjJobMatches(agg, { role: ["devops"] }, today), false, "aggregator jobs stay hidden until their company is selected");
assert.equal(ctx.rjJobMatches(agg, { role: ["devops"], company: ["huzzle"] }, today), true, "selecting the aggregator company reveals its jobs");

function same(actual, expected, name) {
  assert.equal(JSON.stringify(actual), JSON.stringify(expected), name);
}
const raw = "?role=devops,sre&skill=kubernetes,aws&tz=eu-apac&level=senior";
const parsed = ctx.rjParseFacetQuery(raw);
same(parsed.role, ["devops", "sre"]);
same(parsed.skill, ["kubernetes", "aws"]);
same(parsed.tz, ["eu-apac"]);
same(parsed.level, ["senior"]);
assert.equal(ctx.rjSerializeFacetQuery(parsed), "role=devops,sre&skill=kubernetes,aws&tz=eu-apac&level=senior");
same(ctx.rjParseFacetQuery("?" + ctx.rjSerializeFacetQuery(parsed)), parsed, "URL round-trip");
same(ctx.rjParseFacetQuery("?role=devops,,devops,sre").role, ["devops", "sre"], "duplicate and empty values collapse");
const typed = ctx.rjParseFacetQuery("?q=hello+world&role=devops");
assert.equal(typed.q, "hello world");
assert.equal(ctx.rjSerializeFacetQuery(typed), "q=hello%20world&role=devops");

const skillCounts = ctx.rjFacetCounts(jobs, { role: ["devops", "sre"], skill: ["kubernetes"] }, "skill", today);
assert.equal(skillCounts.kubernetes, 1, "skill counts ignore the skill selection");
assert.equal(skillCounts.aws, 2, "aws is on both the devops and sre jobs");
assert.equal(skillCounts.python || 0, 0);
const roleCounts = ctx.rjFacetCounts(jobs, { skill: ["aws"] }, "role", today);
assert.equal(roleCounts.devops, 1, "role counts respect the skill facet");
assert.equal(roleCounts.sre, 1);
assert.equal(roleCounts.backend || 0, 0, "backend has no aws skill");
const sibling = ctx.rjFacetCounts(jobs, { role: ["devops"] }, "role", today);
assert.equal(sibling.sre, 1, "a selected role does not hide sibling role counts");
assert.equal(sibling.backend, 1);

console.log("facet filter tests passed");

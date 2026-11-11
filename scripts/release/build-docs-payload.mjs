#!/usr/bin/env node
/* Builds the payload testzeus-docs consumes from the pull requests behind a
   deploy.

   Only the author-written customer fields cross the boundary — no diffs, no
   commit bodies, no internal description text. That is what lets the docs
   repository treat the payload as publishable source material rather than
   something to be sanitised after the fact.

   A deploy of `main` is a dev -> main promotion. The customer-facing metadata
   ("Add to docs", the release note, affected areas) is written on the feature
   pull requests that were merged into `dev`, not on the promotion itself, so
   the payload is built from every feature pull request the promotion shipped:
   those merged into `dev` after the previous promotion and up to this one. The
   promotion pull request is still read too, for promotions whose own body asks
   for docs.

   Usage:
     node scripts/release/build-docs-payload.mjs > docs-payload.json

   Environment:
     GITHUB_REPOSITORY  owner/repo (set by Actions)
     HEAD_SHA           commit being deployed
     RELEASE            optional release identifier, defaults to YYYY-MM
     GH_TOKEN           token with pull-request read access
     SINCE_SHA          ignored; kept so existing workflows keep working. Walking
                        a tag range re-sent every promotion since the last tag on
                        each deploy.
*/
import { execFileSync } from "node:child_process";

import { parsePrMetadata } from "./lib/parse-pr-body.mjs";

const SHA = /^[0-9a-f]{7,40}$/i;
const repository = process.env.GITHUB_REPOSITORY ?? "";
const headSha = process.env.HEAD_SHA ?? "";
const release = process.env.RELEASE || new Date().toISOString().slice(0, 7);

/* A promotion that ships more feature pull requests than this is not a normal
   release; stop rather than fan out into an unbounded number of API calls. */
const MAX_FEATURE_PRS = 300;

if (!(repository && headSha)) {
  console.error("GITHUB_REPOSITORY and HEAD_SHA are required");
  process.exit(1);
}
if (!SHA.test(headSha)) {
  console.error("HEAD_SHA must be a hex git SHA");
  process.exit(1);
}

const [owner] = repository.split("/");

function ghJson(args) {
  return JSON.parse(execFileSync("gh", ["api", ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }));
}

function isPromotion(pull) {
  return Boolean(pull.merged_at) && pull.base?.ref === "main" && pull.head?.ref === "dev";
}

/** The dev -> main promotion pull request(s) that produced the deployed commit. */
function promotionsForHead() {
  try {
    return ghJson([`repos/${repository}/commits/${headSha}/pulls`]).filter(isPromotion);
  } catch (error) {
    console.error(`Failed to list PRs for ${headSha.slice(0, 7)}: ${error.message.split("\n")[0]}`);
    process.exit(1);
  }
}

/** The promotion merged most recently before `promotion`, if any. */
function previousPromotion(promotion) {
  const merged = [];
  for (let page = 1; page <= 5; page += 1) {
    const pulls = ghJson([
      `repos/${repository}/pulls?state=closed&base=main&head=${owner}:dev&sort=updated&direction=desc&per_page=100&page=${page}`,
    ]);
    merged.push(...pulls.filter((pull) => isPromotion(pull) && pull.merged_at < promotion.merged_at));
    if (pulls.length < 100) {
      break;
    }
  }
  merged.sort((a, b) => b.merged_at.localeCompare(a.merged_at));
  return merged[0];
}

/** Pull requests merged into dev in the window (previous promotion, this promotion]. */
function featurePullsBetween(previous, promotion) {
  const query = `repo:${repository} is:pr is:merged base:dev merged:${previous.merged_at}..${promotion.merged_at}`;
  const found = [];
  for (let page = 1; page <= 10; page += 1) {
    const result = ghJson([
      "-X",
      "GET",
      "search/issues",
      "-f",
      `q=${query}`,
      "-f",
      "per_page=100",
      "-f",
      `page=${page}`,
    ]);
    found.push(...result.items);
    if (result.items.length < 100 || found.length >= MAX_FEATURE_PRS) {
      break;
    }
  }
  if (found.length >= MAX_FEATURE_PRS) {
    console.error(`More than ${MAX_FEATURE_PRS} feature PRs between promotions; refusing to build a payload.`);
    process.exit(1);
  }
  /* The search bounds are inclusive; the previous promotion's own merge second
     belongs to the earlier release. */
  return found.filter((item) => item.pull_request?.merged_at && item.pull_request.merged_at > previous.merged_at);
}

const candidates = new Map();
for (const promotion of promotionsForHead()) {
  candidates.set(promotion.number, {
    number: promotion.number,
    title: promotion.title,
    url: promotion.html_url,
    body: promotion.body,
  });

  const previous = previousPromotion(promotion);
  if (!previous) {
    console.error(`#${promotion.number} is the first promotion; only its own body is read.`);
    continue;
  }
  for (const item of featurePullsBetween(previous, promotion)) {
    if (candidates.has(item.number)) {
      continue;
    }
    candidates.set(item.number, { number: item.number, title: item.title, url: item.html_url, body: item.body });
  }
}

const changes = [];
for (const pull of candidates.values()) {
  const parsed = parsePrMetadata(pull.body ?? "");
  const meta = parsed.metadata;
  /* Allow-list: only valid, customer-facing PRs cross the docs boundary.
     Unclassified and pre-kit bodies are dropped here rather than sent with
     their titles. */
  if (
    !(parsed.valid && meta.docsRequested) ||
    meta.documentationSelectionCount !== 1 ||
    meta.audience !== "customer-facing"
  ) {
    continue;
  }

  const change = {
    pullRequest: pull.number,
    title: pull.title,
    url: pull.url,
    audience: "customer-facing",
    customerReleaseNote: meta.customerReleaseNote || undefined,
    areas: meta.affectedAreas
      ? meta.affectedAreas
          .split(/[,\n]/)
          .map((area) => area.trim())
          .filter(Boolean)
      : undefined,
    changeTypes: meta.changeTypes?.length ? meta.changeTypes : undefined,
    uiChanged: meta.uiChanged,
  };
  if (meta.customerImpact) {
    change.customerImpact = meta.customerImpact;
  }
  changes.push(change);
}

process.stdout.write(
  `${JSON.stringify({ repository: repository.split("/")[1], sha: headSha, release, changes }, null, 2)}\n`,
);
console.error(
  `Built docs payload: ${changes.length} customer-facing change(s) from ${candidates.size} merged PR(s).`,
);

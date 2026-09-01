#!/usr/bin/env node
/* Builds the payload testzeus-docs consumes from the pull requests behind a
   deploy.

   Only the author-written customer fields cross the boundary — no diffs, no
   commit bodies, no internal description text. That is what lets the docs
   repository treat the payload as publishable source material rather than
   something to be sanitised after the fact.

   Usage:
     node scripts/release/build-docs-payload.mjs > docs-payload.json

   Environment:
     GITHUB_REPOSITORY  owner/repo (set by Actions)
     HEAD_SHA           commit being deployed
     SINCE_SHA          optional; walk PRs for every commit in SINCE_SHA..HEAD_SHA
     RELEASE            optional release identifier, defaults to YYYY-MM
     GH_TOKEN           token with pull-request read access
*/
import { execFileSync } from "node:child_process";

import { parsePrMetadata } from "./lib/parse-pr-body.mjs";

const SHA = /^[0-9a-f]{7,40}$/i;
const repository = process.env.GITHUB_REPOSITORY ?? "";
const headSha = process.env.HEAD_SHA ?? "";
const sinceSha = process.env.SINCE_SHA ?? "";
const release = process.env.RELEASE || new Date().toISOString().slice(0, 7);

if (!repository || !headSha) {
  console.error("GITHUB_REPOSITORY and HEAD_SHA are required");
  process.exit(1);
}
if (!SHA.test(headSha)) {
  console.error("HEAD_SHA must be a hex git SHA");
  process.exit(1);
}
if (sinceSha && !SHA.test(sinceSha)) {
  console.error("SINCE_SHA must be a hex git SHA when set");
  process.exit(1);
}

function gh(args) {
  return execFileSync("gh", args, { encoding: "utf8" });
}

/** Commits to inspect. Defaults to the deployed commit alone, which is the
    common case: one squash-merged pull request per deploy. */
function commitsToInspect() {
  if (!sinceSha || sinceSha === headSha) return [headSha];
  try {
    const log = execFileSync("git", ["log", "--first-parent", "--pretty=format:%H", `${sinceSha}..${headSha}`], {
      encoding: "utf8",
    }).trim();
    const commits = log ? log.split("\n") : [];
    /* Bound the walk: a deploy after a long gap should not fan out into
       hundreds of API calls. */
    return commits.slice(0, 50).concat(commits.length ? [] : [headSha]);
  } catch (error) {
    console.error(`git log ${sinceSha}..${headSha} failed: ${error.message.split("\n")[0]}`);
    process.exit(1);
  }
}

const seen = new Map();
for (const sha of commitsToInspect()) {
  let pulls;
  try {
    pulls = JSON.parse(gh(["api", `repos/${repository}/commits/${sha}/pulls`, "--jq", "."]));
  } catch (error) {
    console.error(`Failed to list PRs for ${sha.slice(0, 7)}: ${error.message.split("\n")[0]}`);
    process.exit(1);
  }
  for (const pull of pulls ?? []) {
    if (
      !pull.merged_at ||
      pull.base?.ref !== "main" ||
      pull.head?.ref !== "dev" ||
      seen.has(pull.number)
    ) continue;
    seen.set(pull.number, pull);
  }
}

const changes = [];
for (const pull of seen.values()) {
  const parsed = parsePrMetadata(pull.body ?? "");
  const meta = parsed.metadata;
  /* Allow-list: only valid, customer-facing PRs cross the docs boundary.
     Unclassified and pre-kit bodies are dropped here rather than sent with
     their titles. */
  if (
    !parsed.valid ||
    !meta.docsRequested ||
    meta.documentationSelectionCount !== 1 ||
    meta.audience !== "customer-facing"
  ) continue;

  const change = {
    pullRequest: pull.number,
    title: pull.title,
    url: pull.html_url,
    audience: "customer-facing",
    customerReleaseNote: meta.customerReleaseNote || undefined,
    areas: meta.affectedAreas
      ? meta.affectedAreas.split(/[,\n]/).map((area) => area.trim()).filter(Boolean)
      : undefined,
    changeTypes: meta.changeTypes?.length ? meta.changeTypes : undefined,
    uiChanged: meta.uiChanged,
  };
  if (meta.customerImpact) change.customerImpact = meta.customerImpact;
  changes.push(change);
}

process.stdout.write(
  `${JSON.stringify({ repository: repository.split("/")[1], sha: headSha, release, changes }, null, 2)}\n`,
);
console.error(`Built docs payload: ${changes.length} customer-facing change(s) from ${seen.size} merged PR(s).`);

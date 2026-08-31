#!/usr/bin/env node
import { execFileSync } from "node:child_process";

import {
  areBackmergeOnlyCommits,
  areSyncWaivableCommits,
  listCommitsBetween,
  listFirstParentCommitsBetween,
} from "./lib/backmerge.mjs";
import { extractSyncHead, validatePrSync } from "./lib/pr-sync-marker.mjs";
import { readPrBody } from "./lib/read-pr-body.mjs";

const headSha = process.argv[2] ?? process.env.HEAD_SHA ?? "";
const body = readPrBody(process.argv[3]);
const warnOnly = process.env.RELEASE_METADATA_WARN_ONLY === "true";

const errors = validatePrSync(body, headSha);

if (errors.length > 0) {
  const syncedSha = extractSyncHead(body);

  if (syncedSha && headSha) {
    try {
      const runGit = args => execFileSync("git", args, { encoding: "utf8" }).trim();
      const subjects = listCommitsBetween(syncedSha, headSha, runGit);
      const firstParentSubjects = listFirstParentCommitsBetween(syncedSha, headSha, runGit);

      if (areBackmergeOnlyCommits(subjects)) {
        console.log(
          "::notice ::PR sync waived — only backmerge commits since last description sync",
        );
        process.exit(0);
      }

      // Merging `dev` into a feature branch pulls many base commits into `A..B`, but
      // first-parent history only shows the merge commit itself. Don't force a PR
      // description rewrite for that.
      if (areSyncWaivableCommits(firstParentSubjects)) {
        console.log(
          "::notice ::PR sync waived — only base-merge/backmerge commits on first-parent since last description sync",
        );
        process.exit(0);
      }
    } catch {
      // Git history unavailable — keep validation errors
    }
  }

  for (const error of errors) {
    const prefix = warnOnly ? "::warning ::" : "::error ::";
    console.log(`${prefix}${error}`);
  }

  if (warnOnly) {
    console.log("::notice ::PR description sync validation failed (warn-only mode)");
    process.exit(0);
  }

  console.error(`PR description sync validation failed (${errors.length} issue(s))`);
  process.exit(1);
}

console.log(`PR description sync validation passed (head ${headSha.slice(0, 7)})`);

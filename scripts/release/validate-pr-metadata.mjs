#!/usr/bin/env node
import { isConventionalTitle } from "./lib/conventional.mjs";
import { parsePrMetadata } from "./lib/parse-pr-body.mjs";
import { readPrBody } from "./lib/read-pr-body.mjs";

const title = process.argv[2] ?? process.env.PR_TITLE ?? "";
const body = readPrBody(process.argv[3]);
const warnOnly = process.env.RELEASE_METADATA_WARN_ONLY === "true";
const headRef = process.env.PR_HEAD_REF ?? "";
const baseRef = process.env.PR_BASE_REF ?? "";

const errors = [];

if (!isConventionalTitle(title)) {
  errors.push("PR title must follow Conventional Commits (e.g. feat(scope): description)");
}

const parsed = parsePrMetadata(body);
errors.push(...parsed.errors);

if (baseRef === "main") {
  if (headRef !== "dev") {
    errors.push("Only dev -> main promotion pull requests are allowed");
  } else if (parsed.metadata.documentationSelectionCount !== 1) {
    errors.push("Documentation: select exactly one of Add to docs or No docs update for dev -> main PRs");
  }
}

if (parsed.metadata.docsRequested && parsed.metadata.audience !== "customer-facing") {
  errors.push("Add to docs requires the release classification Customer-facing");
}

if (errors.length > 0) {
  for (const error of errors) {
    const prefix = warnOnly ? "::warning ::" : "::error ::";
    console.log(`${prefix}${error}`);
  }

  if (warnOnly) {
    console.log("::notice ::Release metadata validation failed (warn-only mode)");
    process.exit(0);
  }

  console.error(`Release metadata validation failed (${errors.length} issue(s))`);
  process.exit(1);
}

console.log("Release metadata validation passed");

export const BACKMERGE_TITLE_PREFIX = "Backmerge main to dev";

export const BACKMERGE_COMMIT_REGEX = /^Backmerge main to dev(\s+\[skip ci\])?$/i;

/** e.g. Merge branch 'dev' into feat/foo, Merge remote-tracking branch 'origin/dev' into ... */
export const MERGE_BASE_INTO_FEATURE_REGEX =
  /^Merge (?:branch|remote-tracking branch) ['"]?(?:origin\/)?dev['"]?(?: of \S+)? into .+/i;

export function isBackmergeTitle(title) {
  return String(title ?? "")
    .trim()
    .startsWith(BACKMERGE_TITLE_PREFIX);
}

export function isBackmergeCommitMessage(message) {
  const firstLine = String(message ?? "")
    .trim()
    .split("\n")[0]
    ?.trim();
  return Boolean(firstLine && BACKMERGE_COMMIT_REGEX.test(firstLine));
}

export function isMergeBaseIntoFeatureCommit(message) {
  const firstLine = String(message ?? "")
    .trim()
    .split("\n")[0]
    ?.trim();
  return Boolean(firstLine && MERGE_BASE_INTO_FEATURE_REGEX.test(firstLine));
}

export function isBackmergePullRequest({ title, headRef, authorLogin } = {}) {
  if (isBackmergeTitle(title)) {
    return true;
  }

  if (headRef === "main") {
    return true;
  }

  if (authorLogin === "github-actions[bot]") {
    return true;
  }

  return false;
}

export function listCommitsBetween(baseSha, headSha, runGit) {
  if (!(baseSha && headSha) || baseSha === headSha) {
    return [];
  }

  const output = runGit(["log", `${baseSha}..${headSha}`, "--pretty=format:%s"]);
  if (!output) {
    return [];
  }

  return output.split("\n").filter(Boolean);
}

/** First-parent only — ignores commits brought in by merging base into the feature branch. */
export function listFirstParentCommitsBetween(baseSha, headSha, runGit) {
  if (!(baseSha && headSha) || baseSha === headSha) {
    return [];
  }

  const output = runGit(["log", "--first-parent", `${baseSha}..${headSha}`, "--pretty=format:%s"]);
  if (!output) {
    return [];
  }

  return output.split("\n").filter(Boolean);
}

export function areBackmergeOnlyCommits(subjects) {
  return subjects.length > 0 && subjects.every(isBackmergeCommitMessage);
}

/** True when the only first-parent commits are base merges / backmerges (no feature work). */
export function areSyncWaivableCommits(subjects) {
  return (
    subjects.length > 0 &&
    subjects.every(
      subject => isBackmergeCommitMessage(subject) || isMergeBaseIntoFeatureCommit(subject),
    )
  );
}

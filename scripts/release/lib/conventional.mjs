/* Conventional-commit title rules.

   Kept self-contained so the release kit can be dropped into a repository that
   has no semantic-release setup of its own. The type list matches
   testzeus-hercules-uix's conventional-commit-config.cjs — if a repo adds its
   own release tooling later, point this at that config instead of duplicating
   the list. */

export const ALLOWED_COMMIT_TYPES = [
  "feat",
  "enhancement",
  "fix",
  "perf",
  "revert",
  "security",
  "docs",
  "chore",
  "refactor",
  "style",
  "test",
  "build",
  "ci",
];

const CONVENTIONAL_TITLE_REGEX = new RegExp(
  `^(Merge (branch|remote-tracking branch|pull request)|(${ALLOWED_COMMIT_TYPES.join("|")})(\\([a-zA-Z0-9-]+\\))?!?:).+`,
  "i",
);

export function isConventionalTitle(title) {
  return CONVENTIONAL_TITLE_REGEX.test(String(title ?? "").trim());
}

export function isConventionalCommitMessage(message) {
  const firstLine = String(message ?? "").split("\n")[0]?.trim() ?? "";
  if (/^Merge (branch|remote-tracking branch|pull request)/i.test(firstLine)) return true;
  return isConventionalTitle(firstLine);
}

export const PR_SYNC_MARKER_REGEX = /<!--\s*testzeus-pr-sync-head:\s*([a-f0-9]{7,40})\s*-->/i;

export function buildSyncMarker(headSha) {
  return `<!-- testzeus-pr-sync-head: ${headSha} -->`;
}

export function extractSyncHead(body) {
  const match = body.match(PR_SYNC_MARKER_REGEX);
  return match?.[1]?.toLowerCase() ?? null;
}

export function upsertSyncMarker(body, headSha) {
  const marker = buildSyncMarker(headSha);
  if (PR_SYNC_MARKER_REGEX.test(body)) {
    return body.replace(PR_SYNC_MARKER_REGEX, marker);
  }
  return `${body.trimEnd()}\n\n${marker}\n`;
}

export function validatePrSync(body, headSha) {
  const errors = [];
  const normalizedHead = headSha?.trim().toLowerCase();

  if (!normalizedHead) {
    errors.push("HEAD_SHA is required for PR sync validation");
    return errors;
  }

  const syncedSha = extractSyncHead(body);

  if (!syncedSha) {
    errors.push(
      `PR description must be updated for the latest commits. Refresh What changed, Testing completed, and related sections, then add ${buildSyncMarker(normalizedHead)} to the PR body (or run /sync-pr in Cursor).`,
    );
    return errors;
  }

  if (syncedSha !== normalizedHead) {
    errors.push(
      `PR description is out of date with the latest commits (synced: ${syncedSha.slice(0, 7)}, head: ${normalizedHead.slice(0, 7)}). Update the description accordingly and set ${buildSyncMarker(normalizedHead)}.`,
    );
  }

  return errors;
}

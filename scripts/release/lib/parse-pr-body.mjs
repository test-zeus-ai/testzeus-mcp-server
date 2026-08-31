const PLACEHOLDER_PATTERNS = [
  /^<!--[\s\S]*?-->$/m,
  /^TBD$/i,
  /^TODO$/i,
  /^-$/,
  /^\.{3}$/,
  /^Describe /i,
  /^Provide /i,
  /^Add /i,
  /^List /i,
  /^Link /i,
  /^e\.g\./i,
  /^Write /i,
  /^Flag name/i,
  /^Steps required/i,
  /^How to revert/i,
  /^What you tested/i,
  /^Screenshot,/i,
  /^One sentence customers/i,
  /^Business or technical/i,
  /^Who is affected/i,
];

export function isAllowedOptionalValue(text) {
  return /^(none|n\/a)$/i.test(text.trim());
}

export function isPlaceholder(text, { allowOptionalValues = false } = {}) {
  const trimmed = text.trim();
  if (trimmed.length === 0) {
    return true;
  }
  if (allowOptionalValues && isAllowedOptionalValue(trimmed)) {
    return false;
  }
  if (trimmed.includes("<!--")) {
    return true;
  }
  return PLACEHOLDER_PATTERNS.some(pattern => pattern.test(trimmed));
}

export function extractSection(body, heading) {
  const sections = body.split(/\n(?=## )/);
  const target = `## ${heading}`.toLowerCase();
  let content = "";

  for (const section of sections) {
    const lines = section.split("\n");
    const firstLine = lines[0]?.trim().toLowerCase() ?? "";
    if (firstLine === target) {
      content = lines.slice(1).join("\n").trim();
    }
  }

  return content;
}

const CHECKED_TASK_LINE = /^[-*+]\s+\[\s*[xX]\s*\]\s*(.+)$/;

export function getCheckedOptions(section) {
  const checked = [];
  for (const line of section.split("\n")) {
    const trimmed = line.trim();
    const match = trimmed.match(CHECKED_TASK_LINE);
    if (match) {
      checked.push(match[1].trim());
    }
  }
  return checked;
}

export function requireSection(body, heading, errors, label = heading) {
  const content = extractSection(body, heading);
  if (isPlaceholder(content)) {
    errors.push(`${label} is required`);
  }
  return content;
}

function resolveAudience(isCustomerFacing, isInternalOnly, isReleaseNoteSkip) {
  if (isCustomerFacing) {
    return "customer-facing";
  }
  if (isInternalOnly) {
    return "internal-only";
  }
  if (isReleaseNoteSkip) {
    return "release-note-skip";
  }
  return null;
}

export function parsePrMetadata(body) {
  const errors = [];

  const whatChanged = requireSection(body, "What changed", errors);
  const whyChanged = extractSection(body, "Why was it changed");
  const customerImpact = requireSection(body, "Customer impact", errors);

  const releaseClassification = getCheckedOptions(extractSection(body, "Release classification"));
  if (releaseClassification.length !== 1) {
    errors.push("Release classification: select exactly one option");
  }

  const uiChanges = getCheckedOptions(extractSection(body, "UI changes"));
  if (uiChanges.length === 0) {
    errors.push("UI changes: select at least one option");
  }

  const changeTypes = getCheckedOptions(extractSection(body, "Change type"));
  const documentation = getCheckedOptions(extractSection(body, "Documentation")).filter(option =>
    ["Add to docs", "No docs update"].includes(option),
  );
  const riskLevels = getCheckedOptions(extractSection(body, "Risk"));

  const customerReleaseNote = extractSection(body, "Customer release note");
  const uiEvidence = extractSection(body, "UI evidence");
  const migrationRequirements = extractSection(body, "Migration requirements");
  const testingCompleted = extractSection(body, "Testing completed");

  const isCustomerFacing = releaseClassification.includes("Customer-facing");
  const isInternalOnly = releaseClassification.includes("Internal-only");
  const isReleaseNoteSkip = releaseClassification.includes("Release-note skip");
  const hasUiChange =
    uiChanges.includes("Existing UI changed") ||
    uiChanges.includes("New UI added") ||
    uiChanges.includes("UI removed");
  const isBreaking = changeTypes.includes("Breaking change");
  const isHighRisk = riskLevels.includes("High");

  if (isCustomerFacing && isPlaceholder(customerReleaseNote)) {
    errors.push("Customer release note is required for customer-facing PRs");
  }

  if (hasUiChange && isPlaceholder(uiEvidence, { allowOptionalValues: false })) {
    errors.push("UI evidence is required when UI changes");
  }

  if (!hasUiChange && isPlaceholder(uiEvidence, { allowOptionalValues: true })) {
    // optional section for no-ui PRs
  }

  if (isBreaking) {
    requireSection(body, "Migration requirements", errors);
    requireSection(body, "Rollout plan", errors);
  }

  if (isHighRisk) {
    const rollback = extractSection(body, "Rollback plan");
    if (isPlaceholder(rollback, { allowOptionalValues: false })) {
      errors.push("Rollback plan is required for high-risk changes");
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    metadata: {
      whatChanged,
      whyChanged,
      customerImpact,
      customerReleaseNote,
      releaseClassification: releaseClassification[0] ?? null,
      uiChanges,
      changeTypes,
      riskLevels: riskLevels[0] ?? null,
      affectedAreas: extractSection(body, "Affected areas"),
      featureFlags: extractSection(body, "Feature flags"),
      configurationChanges: extractSection(body, "Configuration changes"),
      migrationRequirements,
      migrationRequired:
        isBreaking ||
        !(
          isPlaceholder(migrationRequirements, { allowOptionalValues: true }) ||
          /^(none|n\/a)$/i.test(migrationRequirements.trim())
        ),
      rollout: extractSection(body, "Rollout plan"),
      rollback: extractSection(body, "Rollback plan"),
      testingCompleted,
      uiChanged: hasUiChange,
      audience: resolveAudience(isCustomerFacing, isInternalOnly, isReleaseNoteSkip),
      type: inferChangeType(changeTypes),
      docsRequested: documentation.includes("Add to docs"),
      documentationSelectionCount: documentation.length,
    },
  };
}

function inferChangeType(changeTypes) {
  if (changeTypes.includes("Breaking change")) {
    return "breaking";
  }
  if (changeTypes.includes("Feature")) {
    return "feature";
  }
  if (changeTypes.includes("Bug fix")) {
    return "fix";
  }
  if (changeTypes.includes("Performance")) {
    return "performance";
  }
  if (changeTypes.includes("Infrastructure")) {
    return "infrastructure";
  }
  if (changeTypes.includes("Documentation")) {
    return "documentation";
  }
  if (changeTypes.includes("Refactor")) {
    return "refactor";
  }
  return "other";
}

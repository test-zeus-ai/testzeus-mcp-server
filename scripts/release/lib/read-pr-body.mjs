import { readFileSync } from "node:fs";

export function readPrBody(argvValue, env = process.env) {
  if (typeof argvValue === "string" && argvValue.length > 0) {
    return argvValue;
  }
  if (env.PR_BODY_FILE) {
    return readFileSync(env.PR_BODY_FILE, "utf8");
  }
  return env.PR_BODY ?? "";
}

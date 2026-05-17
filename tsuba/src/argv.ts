/**
 * Argv parsing for the tsuba CLI.
 *
 *   tsuba -- <program> [args...]
 *
 * v1: no flags on tsuba itself; the '--' separator is mandatory and
 * the inner command must be non-empty.
 */

const USAGE = "Usage: tsuba -- <program> [args...]";

export class UsageError extends Error {
  constructor(message: string) {
    super(`${message}\n${USAGE}`);
    this.name = "UsageError";
  }
}

export interface ParsedArgv {
  innerCommand: string[];
}

/**
 * @param argv Typically `process.argv` — `[node, scriptPath, ...rest]`.
 */
export function parseArgv(argv: string[]): ParsedArgv {
  // argv[0] = node, argv[1] = entry script — drop both.
  const userArgs = argv.slice(2);
  const sepIndex = userArgs.indexOf("--");

  if (sepIndex === -1) {
    throw new UsageError("missing '--' separator");
  }
  if (sepIndex !== 0) {
    throw new UsageError("tsuba does not accept arguments before '--' in v1");
  }

  const innerCommand = userArgs.slice(sepIndex + 1);
  if (innerCommand.length === 0) {
    throw new UsageError("no program supplied after '--'");
  }

  return { innerCommand };
}

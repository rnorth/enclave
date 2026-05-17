import { describe, it, expect } from "vitest";
import { parseArgv, UsageError } from "../src/argv.js";

describe("parseArgv", () => {
  it("returns the inner command after --", () => {
    const result = parseArgv(["node", "tsuba", "--", "pi"]);
    expect(result.innerCommand).toEqual(["pi"]);
  });

  it("passes through everything after -- including flags", () => {
    const result = parseArgv(["node", "tsuba", "--", "pi", "--foo", "bar"]);
    expect(result.innerCommand).toEqual(["pi", "--foo", "bar"]);
  });

  it("throws UsageError when -- is missing", () => {
    expect(() => parseArgv(["node", "tsuba", "pi"])).toThrowError(UsageError);
  });

  it("throws UsageError when nothing follows --", () => {
    expect(() => parseArgv(["node", "tsuba", "--"])).toThrowError(UsageError);
  });

  it("rejects any tsuba args before '--' in v1", () => {
    expect(() => parseArgv(["node", "tsuba", "--config", "x", "--", "pi"]))
      .toThrowError(UsageError);
  });

  it("UsageError carries the expected usage line", () => {
    try {
      parseArgv(["node", "tsuba"]);
      throw new Error("expected UsageError");
    } catch (err) {
      expect(err).toBeInstanceOf(UsageError);
      expect((err as UsageError).message).toContain("tsuba -- <program>");
    }
  });
});

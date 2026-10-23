import { describe, expect, it } from "vitest";
import { DateTime } from "luxon";
import {
  clock,
  departureOptions,
  duration,
  futureDeparture,
  validateDeparture,
} from "./utils";

describe("departure scheduling", () => {
  it("sends an offset-aware instant from the origin timezone, independent of browser timezone", () => {
    const result = validateDeparture(
      "2026-10-23T09:00",
      "America/Chicago",
      null,
      DateTime.fromISO("2026-10-23T12:00:00Z"),
    );
    expect(result.iso).toBe("2026-10-23T09:00:00.000-05:00");
    expect(DateTime.fromISO(result.iso!).toUTC().hour).toBe(14);
  });
  it("rejects a nonexistent local time instead of silently shifting it across DST", () => {
    expect(departureOptions("2026-03-08T02:30", "America/Chicago")).toEqual([]);
    expect(
      validateDeparture("2026-03-08T02:30", "America/Chicago", null).error,
    ).toContain("does not exist");
  });
  it("requires explicit selection when the same local time occurs twice", () => {
    const now = DateTime.fromISO("2026-10-31T12:00Z");
    const options = departureOptions("2026-11-01T01:30", "America/Chicago");
    expect(options.map((item) => item.offset)).toEqual([-300, -360]);
    expect(
      validateDeparture("2026-11-01T01:30", "America/Chicago", null, now).error,
    ).toContain("occurs twice");
    const first = validateDeparture(
      "2026-11-01T01:30",
      "America/Chicago",
      -300,
      now,
    );
    const second = validateDeparture(
      "2026-11-01T01:30",
      "America/Chicago",
      -360,
      now,
    );
    expect(
      DateTime.fromISO(second.iso!).toMillis() -
        DateTime.fromISO(first.iso!).toMillis(),
    ).toBe(3600000);
  });
  it("limits departure to the next 48 hours", () => {
    const now = DateTime.fromISO("2026-10-23T12:00Z");
    expect(
      validateDeparture("2026-10-23T06:00", "America/Chicago", null, now).error,
    ).toContain("next 48 hours");
    expect(
      validateDeparture("2026-10-25T07:01", "America/Chicago", null, now).error,
    ).toContain("next 48 hours");
    expect(
      validateDeparture("2026-10-25T07:00", "America/Chicago", null, now).iso,
    ).toBeDefined();
  });
  it("uses a future hour in the origin timezone by default", () => {
    expect(
      futureDeparture(
        "America/Chicago",
        DateTime.fromISO("2026-10-23T12:34:45Z"),
      ),
    ).toBe("2026-10-23T08:34");
  });
});

describe("route presentation", () => {
  it("rounds duration without producing a 60-minute remainder", () => {
    expect(duration(7199)).toBe("2h 00m");
    expect(duration(19800)).toBe("5h 30m");
  });
  it("shows destination local time with the timezone abbreviation", () => {
    expect(clock("2026-10-23T13:00:00-05:00", "America/Detroit")).toBe(
      "2:00 PM EDT",
    );
  });
});

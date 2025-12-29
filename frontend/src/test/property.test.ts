import fc from "fast-check";

describe("Property-based tests", () => {
  it("should demonstrate array length property", () => {
    fc.assert(
      fc.property(fc.array(fc.integer()), (arr) => {
        // Property: Array length is always non-negative
        // **Feature: health-insight-core, Property Example: Array length non-negative**
        expect(arr.length).toBeGreaterThanOrEqual(0);
      })
    );
  });

  it("should demonstrate string concatenation property", () => {
    fc.assert(
      fc.property(fc.string(), fc.string(), (a, b) => {
        // Property: String concatenation length equals sum of individual lengths
        // **Feature: health-insight-core, Property Example: String concatenation length**
        const result = a + b;
        expect(result.length).toBe(a.length + b.length);
      })
    );
  });
});

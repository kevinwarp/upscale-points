import {
  calculateGmvScore,
  calculateRecognitionScore,
  calculateTier,
} from "../src/services/scoring.service";
import { getIndustryScore } from "../src/utils/industry";

describe("calculateGmvScore", () => {
  it("returns 1 for $0-5M", () => {
    expect(calculateGmvScore(0)).toBe(1);
    expect(calculateGmvScore(4_999_999)).toBe(1);
  });

  it("returns 2 for $5M-10M (inclusive lower bound)", () => {
    expect(calculateGmvScore(5_000_000)).toBe(2);
    expect(calculateGmvScore(9_999_999)).toBe(2);
  });

  it("returns 3 for $10M-25M", () => {
    expect(calculateGmvScore(10_000_000)).toBe(3);
    expect(calculateGmvScore(24_999_999)).toBe(3);
  });

  it("returns 4 for $25M-100M", () => {
    expect(calculateGmvScore(25_000_000)).toBe(4);
    expect(calculateGmvScore(99_999_999)).toBe(4);
  });

  it("returns 5 for $100M+", () => {
    expect(calculateGmvScore(100_000_000)).toBe(5);
    expect(calculateGmvScore(500_000_000)).toBe(5);
  });
});

describe("getIndustryScore", () => {
  it("returns 3 for high-value industries", () => {
    expect(getIndustryScore("Beauty")).toEqual({ score: 3, matched: true });
    expect(getIndustryScore("Furniture")).toEqual({ score: 3, matched: true });
    expect(getIndustryScore("Health & Wellness")).toEqual({ score: 3, matched: true });
    expect(getIndustryScore("Supplements")).toEqual({ score: 3, matched: true });
  });

  it("returns 1 for standard industries", () => {
    expect(getIndustryScore("Apparel")).toEqual({ score: 1, matched: true });
    expect(getIndustryScore("Jewelry")).toEqual({ score: 1, matched: true });
    expect(getIndustryScore("Food & Beverage")).toEqual({ score: 1, matched: true });
    expect(getIndustryScore("CPG")).toEqual({ score: 1, matched: true });
  });

  it("is case-insensitive", () => {
    expect(getIndustryScore("BEAUTY")).toEqual({ score: 3, matched: true });
    expect(getIndustryScore("beauty")).toEqual({ score: 3, matched: true });
  });

  it("supports partial matches", () => {
    expect(getIndustryScore("Health")).toEqual({ score: 3, matched: true });
    expect(getIndustryScore("Food")).toEqual({ score: 1, matched: true });
  });

  it("returns 1 with matched=false for unknown categories", () => {
    expect(getIndustryScore("Technology")).toEqual({ score: 1, matched: false });
    expect(getIndustryScore(null)).toEqual({ score: 1, matched: false });
  });
});

describe("calculateRecognitionScore", () => {
  it("returns 0 when neither flag is set", () => {
    expect(calculateRecognitionScore(false, false)).toBe(0);
  });

  it("returns 1 when only known brand", () => {
    expect(calculateRecognitionScore(true, false)).toBe(1);
  });

  it("returns 2 when both flags set", () => {
    expect(calculateRecognitionScore(true, true)).toBe(2);
  });

  it("returns 0 when only recognized exec (no known brand)", () => {
    expect(calculateRecognitionScore(false, true)).toBe(0);
  });
});

describe("calculateTier", () => {
  it("maps score ranges to correct tiers", () => {
    expect(calculateTier(10)).toBe("Tier 1");
    expect(calculateTier(9)).toBe("Tier 1");
    expect(calculateTier(8)).toBe("Tier 2");
    expect(calculateTier(7)).toBe("Tier 2");
    expect(calculateTier(6)).toBe("Tier 3");
    expect(calculateTier(5)).toBe("Tier 3");
    expect(calculateTier(4)).toBe("Tier 4");
    expect(calculateTier(3)).toBe("Tier 4");
    expect(calculateTier(2)).toBe("Tier 5");
    expect(calculateTier(1)).toBe("Tier 5");
  });
});

describe("end-to-end score calculations", () => {
  it("calculates max score (Tier 1)", () => {
    const gmv = calculateGmvScore(162_000_000); // 5
    const { score: industry } = getIndustryScore("Beauty"); // 3
    const recognition = calculateRecognitionScore(true, true); // 2
    const total = gmv + industry + recognition;
    expect(total).toBe(10);
    expect(calculateTier(total)).toBe("Tier 1");
  });

  it("calculates min score (Tier 5)", () => {
    const gmv = calculateGmvScore(0); // 1
    const { score: industry } = getIndustryScore(null); // 1
    const recognition = calculateRecognitionScore(false, false); // 0
    const total = gmv + industry + recognition;
    expect(total).toBe(2);
    expect(calculateTier(total)).toBe("Tier 5");
  });

  it("calculates mid-range score", () => {
    const gmv = calculateGmvScore(15_000_000); // 3
    const { score: industry } = getIndustryScore("Apparel"); // 1
    const recognition = calculateRecognitionScore(true, false); // 1
    const total = gmv + industry + recognition;
    expect(total).toBe(5);
    expect(calculateTier(total)).toBe("Tier 3");
  });
});

const THREE_POINT_INDUSTRIES = [
  "beauty",
  "furniture",
  "health & wellness",
  "health",
  "wellness",
  "supplements",
];

const ONE_POINT_INDUSTRIES = [
  "apparel",
  "jewelry",
  "food & beverage",
  "food",
  "beverage",
  "cpg",
];

export function getIndustryScore(category: string | null): {
  score: number;
  matched: boolean;
} {
  if (!category) {
    return { score: 1, matched: false };
  }

  const normalized = category.toLowerCase().trim();

  if (THREE_POINT_INDUSTRIES.some((ind) => normalized.includes(ind))) {
    return { score: 3, matched: true };
  }

  if (ONE_POINT_INDUSTRIES.some((ind) => normalized.includes(ind))) {
    return { score: 1, matched: true };
  }

  return { score: 1, matched: false };
}

/**
 * TypeScript type definitions for Competitor Comparison Pages
 *
 * These types ensure consistency across all competitor data files,
 * page content, and React components.
 */

export interface CompanyInfo {
  name: string;
  website: string;
  founded: number;
  headquarters: string;
  tagline: string;
}

export interface Pricing {
  model: string; // "fixed-monthly" | "percentage-of-collections" | "roi-based" | "custom"
  startingPrice?: string; // e.g., "$500/month" or "Contact sales"
  currency?: string;
  billingFrequency?: string; // "monthly" | "annual"
  freeTier: boolean;
  freeTierLimits?: string;
  enterprise: boolean;
  enterpriseStartsAt?: string;
  transparency: "high" | "medium" | "low"; // How transparent is their pricing?
  notes?: string[];
}

export interface FeatureRating {
  rating: number; // 1-5 scale
  description: string;
  details?: string[];
}

export interface Features {
  payerBehaviorMonitoring: FeatureRating;
  earlyWarningSignals: FeatureRating;
  denialPrevention: FeatureRating;
  realTimeAlerts: FeatureRating;
  specialtySpecificRules: FeatureRating;
  ehrIntegration: FeatureRating;
  claimsManagement: FeatureRating;
  analytics: FeatureRating;
  reporting: FeatureRating;
  apiAccess: FeatureRating;
}

export interface Implementation {
  averageTimeline: string; // e.g., "30 days" | "3-6 months" | "EHR-dependent"
  complexity: "low" | "medium" | "high";
  requiresEHRIntegration: boolean;
  supportedEHRs?: string[];
  dataConnectionMethod: string; // e.g., "API" | "SFTP" | "Manual upload" | "EHR embedded"
  onboardingSupport: string;
}

export interface Support {
  channels: string[]; // e.g., ["Email", "Phone", "Chat", "Dedicated CSM"]
  responseTime?: string; // SLA if known
  documentation: "excellent" | "good" | "fair" | "poor";
  onboardingIncluded: boolean;
  trainingIncluded: boolean;
}

export interface TargetMarket {
  primarySegments: string[];
  idealCustomerSize: string; // e.g., "5-50 providers" | "Enterprise (500+)"
  industryFocus: string[];
  geographicFocus?: string;
}

export interface CompetitorData {
  company: CompanyInfo;
  positioning: {
    valueProposition: string;
    keyDifferentiator: string;
    primaryUseCase: string;
    marketPosition: string; // e.g., "Mid-market leader" | "Enterprise player"
  };
  pricing: Pricing;
  features: Features;
  implementation: Implementation;
  support: Support;
  target: TargetMarket;
  strengths: string[];
  weaknesses: string[];
  bestFor: string[];
  notIdealFor: string[];
  commonComplaints?: string[]; // From G2, Capterra, customer feedback
  commonPraise?: string[]; // From reviews
  competitiveIntel: {
    marketShare?: string;
    customerCount?: string;
    recentFunding?: string;
    recentChanges?: string[]; // Product updates, leadership changes, etc.
  };
}

export interface ProductData extends CompetitorData {
  // Upstream-specific extensions
  products: {
    name: string;
    description: string;
    status: "GA" | "Beta" | "Coming Soon";
  }[];
}

export interface ComparisonCategory {
  name: string;
  weight: number; // 1-5, importance for decision-making
  subcategories: {
    name: string;
    description: string;
    upstreamValue: string | number;
    competitorValue: string | number;
    winner?: "upstream" | "competitor" | "tie";
    notes?: string;
  }[];
}

export interface MigrationInfo {
  fromCompetitor: string;
  difficulty: "easy" | "medium" | "hard";
  estimatedTimeline: string;
  whatTransfers: string[];
  whatDoesntTransfer: string[];
  migrationSupport: string;
  commonChallenges?: string[];
  tips?: string[];
}

export interface BattleCard {
  competitor: string;
  lastUpdated: string;
  executiveSummary: string;
  quickWins: {
    claim: string;
    proof: string;
    impact: string;
  }[];
  objections: {
    objection: string;
    acknowledge: string;
    reframe: string;
    bridge: string;
    prove: string;
    ask: string;
  }[];
  discoveryQuestions: string[];
  whenToCompeteAggressively: string[];
  whenToConcede: string[];
  proofPoints: {
    type: "case-study" | "testimonial" | "metric" | "award";
    content: string;
    source?: string;
  }[];
}

export interface SEOMetadata {
  title: string;
  description: string;
  keywords: string[];
  canonicalUrl: string;
  ogImage?: string;
  schema?: Record<string, any>; // JSON-LD schema
}

export interface PageContent {
  slug: string;
  type: "vs-comparison" | "alternative" | "alternatives-plural" | "competitor-vs-competitor";
  metadata: SEOMetadata;
  competitors: string[]; // Company names being compared
  lastUpdated: string;
  content: string; // MDX content
}

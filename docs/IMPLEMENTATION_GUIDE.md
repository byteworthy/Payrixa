# Next.js Implementation Guide

**Last Updated:** January 26, 2026
**Target Framework:** Next.js 14+ (App Router)

---

## Overview

This guide walks through implementing competitor comparison pages in your Next.js marketing site using the content files and components provided in this repository.

---

## Prerequisites

- Next.js 14+ with App Router
- TypeScript
- Tailwind CSS (for component styling)
- MDX support (`@next/mdx` or `next-mdx-remote`)
- lucide-react (for icons - or substitute with your icon library)

---

## Step 1: Directory Structure Setup

Create the following directory structure in your Next.js project:

```
/upstream-marketing-nextjs/
├── /app/
│   ├── /competitors/
│   │   ├── page.tsx                    # Index/hub page (future)
│   │   └── /[slug]/
│   │       └── page.tsx                # Dynamic route for comparison pages
│   └── /alternatives/
│       ├── page.tsx                    # Index/hub page (future)
│       └── /[slug]/
│           └── page.tsx                # Dynamic route for alternative pages
├── /components/
│   └── /competitors/
│       ├── ComparisonTable.tsx
│       ├── PricingComparison.tsx
│       ├── FeatureSpotlight.tsx
│       ├── MigrationTimeline.tsx
│       ├── CTASection.tsx
│       └── SocialProof.tsx
├── /content/
│   └── /competitors/
│       ├── /data/
│       │   ├── adonis-intelligence.json
│       │   ├── upstream.json
│       │   └── comparison-framework.json
│       ├── vs-adonis.mdx
│       └── /alternatives/
│           └── adonis.mdx
├── /lib/
│   └── competitors.ts                   # Data loading utilities
└── /public/
    └── /og-images/
        ├── vs-adonis.png
        └── adonis-alternative.png
```

---

## Step 2: Data Loading Utilities

Create `/lib/competitors.ts` for loading competitor data and content:

```typescript
// /lib/competitors.ts

import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { serialize } from 'next-mdx-remote/serialize';

export interface CompetitorData {
  company: {
    name: string;
    founded?: string;
    headquarters?: string;
    website?: string;
    tagline?: string;
  };
  positioning: any;
  pricing: any;
  features: any;
  strengths: string[];
  weaknesses: string[];
  bestFor: string[];
  notIdealFor: string[];
}

export interface ComparisonContent {
  slug: string;
  title: string;
  description: string;
  metaDescription: string;
  openGraph: {
    title: string;
    description: string;
    image: string;
  };
  keywords: string[];
  body: any; // MDX serialized content
}

/**
 * Get competitor data from JSON file
 */
export function getCompetitorData(slug: string): CompetitorData {
  const filePath = path.join(
    process.cwd(),
    'content/competitors/data',
    `${slug}.json`
  );

  if (!fs.existsSync(filePath)) {
    throw new Error(`Competitor data not found: ${slug}`);
  }

  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents);
}

/**
 * Get comparison page content (MDX)
 */
export async function getComparisonContent(
  slug: string
): Promise<ComparisonContent> {
  const filePath = path.join(
    process.cwd(),
    'content/competitors',
    `${slug}.mdx`
  );

  if (!fs.existsSync(filePath)) {
    throw new Error(`Comparison content not found: ${slug}`);
  }

  const fileContents = fs.readFileSync(filePath, 'utf8');
  const { data, content } = matter(fileContents);

  // Serialize MDX content
  const mdxSource = await serialize(content);

  return {
    slug: data.slug || slug,
    title: data.title,
    description: data.description,
    metaDescription: data.metaDescription,
    openGraph: data.openGraph,
    keywords: data.keywords || [],
    body: mdxSource,
  };
}

/**
 * Get alternative page content (MDX)
 */
export async function getAlternativeContent(
  slug: string
): Promise<ComparisonContent> {
  const filePath = path.join(
    process.cwd(),
    'content/competitors/alternatives',
    `${slug}.mdx`
  );

  if (!fs.existsSync(filePath)) {
    throw new Error(`Alternative content not found: ${slug}`);
  }

  const fileContents = fs.readFileSync(filePath, 'utf8');
  const { data, content } = matter(fileContents);

  const mdxSource = await serialize(content);

  return {
    slug: data.slug || slug,
    title: data.title,
    description: data.description,
    metaDescription: data.metaDescription,
    openGraph: data.openGraph,
    keywords: data.keywords || [],
    body: mdxSource,
  };
}

/**
 * Get comparison framework
 */
export function getComparisonFramework() {
  const filePath = path.join(
    process.cwd(),
    'content/competitors/data',
    'comparison-framework.json'
  );

  const fileContents = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(fileContents);
}

/**
 * Get all comparison page slugs (for static generation)
 */
export function getAllComparisonSlugs(): string[] {
  const contentDir = path.join(process.cwd(), 'content/competitors');
  const files = fs.readdirSync(contentDir);

  return files
    .filter((file) => file.endsWith('.mdx'))
    .map((file) => file.replace('.mdx', ''));
}

/**
 * Get all alternative page slugs (for static generation)
 */
export function getAllAlternativeSlugs(): string[] {
  const contentDir = path.join(
    process.cwd(),
    'content/competitors/alternatives'
  );
  const files = fs.readdirSync(contentDir);

  return files
    .filter((file) => file.endsWith('.mdx'))
    .map((file) => file.replace('.mdx', ''));
}
```

---

## Step 3: Dynamic Comparison Page Route

Create `/app/competitors/[slug]/page.tsx`:

```typescript
// /app/competitors/[slug]/page.tsx

import { Metadata } from 'next';
import { MDXRemote } from 'next-mdx-remote/rsc';
import {
  getComparisonContent,
  getCompetitorData,
  getComparisonFramework,
  getAllComparisonSlugs,
} from '@/lib/competitors';
import ComparisonTable from '@/components/competitors/ComparisonTable';
import PricingComparison from '@/components/competitors/PricingComparison';
import FeatureSpotlight from '@/components/competitors/FeatureSpotlight';
import MigrationTimeline from '@/components/competitors/MigrationTimeline';
import CTASection from '@/components/competitors/CTASection';
import SocialProof from '@/components/competitors/SocialProof';

// Static generation for all comparison pages
export async function generateStaticParams() {
  const slugs = getAllComparisonSlugs();
  return slugs.map((slug) => ({ slug }));
}

// Generate SEO metadata
export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const content = await getComparisonContent(params.slug);

  return {
    title: content.title,
    description: content.metaDescription,
    keywords: content.keywords,
    openGraph: {
      title: content.openGraph.title,
      description: content.openGraph.description,
      images: [content.openGraph.image],
      type: 'article',
    },
    alternates: {
      canonical: `https://upstream.com/competitors/${params.slug}`,
    },
  };
}

// Page component
export default async function ComparisonPage({
  params,
}: {
  params: { slug: string };
}) {
  const content = await getComparisonContent(params.slug);
  const competitorSlug = content.slug.replace('vs-', '');
  const upstreamData = getCompetitorData('upstream');
  const competitorData = getCompetitorData(competitorSlug);
  const comparisonFramework = getComparisonFramework();

  // Custom MDX components (inject React components into MDX)
  const components = {
    ComparisonTable: () => (
      <ComparisonTable
        upstream={upstreamData}
        competitor={competitorData}
        categories={comparisonFramework.comparisonCategories}
        highlightUpstream={true}
      />
    ),
    PricingComparison: () => (
      <PricingComparison
        upstream={upstreamData}
        competitor={competitorData}
        showCalculator={true}
      />
    ),
    FeatureSpotlight: (props: any) => (
      <FeatureSpotlight
        {...props}
        upstreamDetails={{
          companyName: upstreamData.company.name,
          ...props.upstreamDetails,
        }}
        competitorDetails={{
          companyName: competitorData.company.name,
          ...props.competitorDetails,
        }}
      />
    ),
    MigrationTimeline: () => (
      <MigrationTimeline
        competitorName={competitorData.company.name}
        timeline="30"
        fastTrack={true}
        parallelOperation={true}
      />
    ),
    CTASection: (props: any) => (
      <CTASection
        {...props}
        competitorName={competitorData.company.name}
      />
    ),
    SocialProof: (props: any) => <SocialProof {...props} />,
  };

  return (
    <article className="competitor-comparison-page max-w-5xl mx-auto px-4 py-12">
      {/* JSON-LD Schema for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            name: content.title,
            description: content.description,
            mainEntity: {
              '@type': 'FAQPage',
              mainEntity: [
                {
                  '@type': 'Question',
                  name: `What's the difference between ${upstreamData.company.name} and ${competitorData.company.name}?`,
                  acceptedAnswer: {
                    '@type': 'Answer',
                    text: content.description,
                  },
                },
              ],
            },
          }),
        }}
      />

      {/* MDX Content with custom components */}
      <MDXRemote source={content.body} components={components} />
    </article>
  );
}
```

---

## Step 4: Dynamic Alternative Page Route

Create `/app/alternatives/[slug]/page.tsx`:

```typescript
// /app/alternatives/[slug]/page.tsx

import { Metadata } from 'next';
import { MDXRemote } from 'next-mdx-remote/rsc';
import {
  getAlternativeContent,
  getCompetitorData,
  getAllAlternativeSlugs,
} from '@/lib/competitors';
import ComparisonTable from '@/components/competitors/ComparisonTable';
import PricingComparison from '@/components/competitors/PricingComparison';
import MigrationTimeline from '@/components/competitors/MigrationTimeline';
import CTASection from '@/components/competitors/CTASection';
import SocialProof from '@/components/competitors/SocialProof';

export async function generateStaticParams() {
  const slugs = getAllAlternativeSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const content = await getAlternativeContent(params.slug);

  return {
    title: content.title,
    description: content.metaDescription,
    keywords: content.keywords,
    openGraph: {
      title: content.openGraph.title,
      description: content.openGraph.description,
      images: [content.openGraph.image],
      type: 'article',
    },
    alternates: {
      canonical: `https://upstream.com/alternatives/${params.slug}`,
    },
  };
}

export default async function AlternativePage({
  params,
}: {
  params: { slug: string };
}) {
  const content = await getAlternativeContent(params.slug);
  const competitorSlug = params.slug;
  const upstreamData = getCompetitorData('upstream');
  const competitorData = getCompetitorData(competitorSlug);

  const components = {
    ComparisonTable: () => (
      <ComparisonTable
        upstream={upstreamData}
        competitor={competitorData}
        categories={[]}
        highlightUpstream={true}
      />
    ),
    PricingComparison: () => (
      <PricingComparison
        upstream={upstreamData}
        competitor={competitorData}
        showCalculator={true}
      />
    ),
    MigrationTimeline: () => (
      <MigrationTimeline
        competitorName={competitorData.company.name}
        timeline="30"
        fastTrack={true}
        parallelOperation={true}
      />
    ),
    CTASection: (props: any) => (
      <CTASection
        {...props}
        competitorName={competitorData.company.name}
      />
    ),
    SocialProof: (props: any) => <SocialProof {...props} />,
  };

  return (
    <article className="alternative-page max-w-5xl mx-auto px-4 py-12">
      {/* JSON-LD Schema for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            name: content.title,
            description: content.description,
          }),
        }}
      />

      <MDXRemote source={content.body} components={components} />
    </article>
  );
}
```

---

## Step 5: Install Dependencies

```bash
# MDX support
npm install @next/mdx @mdx-js/loader @mdx-js/react
npm install next-mdx-remote gray-matter

# Icons (if not already installed)
npm install lucide-react

# TypeScript types
npm install --save-dev @types/mdx
```

---

## Step 6: Configure Next.js for MDX

Update `next.config.js`:

```javascript
// next.config.js

const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [],
    rehypePlugins: [],
  },
});

module.exports = withMDX({
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],
  // ... other config
});
```

---

## Step 7: Add Internal Linking

Update your navigation or sitemap to include competitor pages:

```tsx
// Example: Add to main navigation or sitemap

const competitorLinks = [
  {
    label: 'Upstream vs Adonis',
    href: '/competitors/vs-adonis',
  },
  {
    label: 'Adonis Alternative',
    href: '/alternatives/adonis',
  },
  // Add more as you create them
];
```

Link from relevant product pages:

```tsx
// Example: Link from product page or blog post

<Link href="/competitors/vs-adonis">
  See how Upstream compares to Adonis Intelligence
</Link>
```

---

## Step 8: Generate Open Graph Images

Create Open Graph images for social sharing:

1. Design 1200x630px images for each comparison page
2. Save to `/public/og-images/`
   - `/public/og-images/vs-adonis.png`
   - `/public/og-images/adonis-alternative.png`

Include:
- Upstream logo
- Competitor logo
- Page title ("Upstream vs Adonis Intelligence")
- Key differentiator (e.g., "30-day implementation vs 3-6 months")

---

## Step 9: Test Locally

```bash
# Run Next.js dev server
npm run dev

# Visit pages
http://localhost:3000/competitors/vs-adonis
http://localhost:3000/alternatives/adonis
```

Test:
- Page loads correctly
- MDX content renders
- Components display properly
- Mobile responsiveness
- Internal links work
- SEO metadata in <head> (view source)

---

## Step 10: Deploy to Staging

```bash
# Build for production
npm run build

# Deploy to staging environment (Vercel, Netlify, etc.)
vercel --prod --target=staging
```

Run pre-launch checks (see `SEO_OPTIMIZATION_GUIDE.md`):
- Google Rich Results Test
- Lighthouse audit
- Mobile-friendly test
- Broken link checker

---

## Step 11: Launch to Production

After validation:

```bash
# Deploy to production
vercel --prod
```

Post-launch:
- Monitor Google Search Console for indexing
- Track rankings for target keywords ("Upstream vs Adonis", "Adonis alternative")
- Monitor analytics (bounce rate, time on page, conversions)

---

## Troubleshooting

### Issue: MDX not rendering

**Solution:** Ensure `next-mdx-remote` is installed and MDX files have correct frontmatter.

### Issue: Components not displaying in MDX

**Solution:** Check that component names in MDX match the `components` object keys in the page.

### Issue: JSON data not loading

**Solution:** Verify file paths in `lib/competitors.ts` match your actual directory structure.

### Issue: Build fails with "Can't find module"

**Solution:** Ensure all imports use correct paths (relative vs. absolute with `@/` alias).

### Issue: Styling broken

**Solution:** Verify Tailwind CSS is configured and purging is set correctly for `/components/**/*.tsx`.

---

## Performance Optimization

### Static Generation

All competitor pages should be statically generated at build time for optimal performance:

```typescript
// generateStaticParams ensures static generation
export async function generateStaticParams() {
  return [{ slug: 'vs-adonis' }];
}
```

### Image Optimization

Use Next.js `<Image>` component for all images:

```tsx
import Image from 'next/image';

<Image
  src="/og-images/vs-adonis.png"
  alt="Upstream vs Adonis comparison"
  width={1200}
  height={630}
  priority
/>
```

### Code Splitting

Components are automatically code-split by Next.js. For further optimization, use dynamic imports:

```typescript
import dynamic from 'next/dynamic';

const ComparisonTable = dynamic(
  () => import('@/components/competitors/ComparisonTable'),
  { loading: () => <p>Loading...</p> }
);
```

---

## Maintenance

### Adding New Competitors

1. Create competitor data JSON: `/content/competitors/data/new-competitor.json`
2. Create comparison page MDX: `/content/competitors/vs-new-competitor.mdx`
3. Create alternative page MDX: `/content/competitors/alternatives/new-competitor.mdx`
4. Generate Open Graph images: `/public/og-images/vs-new-competitor.png`
5. Rebuild and deploy

### Updating Existing Competitor Data

1. Edit JSON file: `/content/competitors/data/adonis-intelligence.json`
2. Edit MDX content: `/content/competitors/vs-adonis.mdx`
3. Rebuild and deploy (static pages will regenerate)

---

## Support

For implementation questions:
- **Technical:** dev@upstream.com
- **Content:** marketing@upstream.com
- **SEO:** seo@upstream.com

---

**Document Version:** 1.0
**Last Updated:** January 26, 2026

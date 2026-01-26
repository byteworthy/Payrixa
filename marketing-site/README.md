# Upstream Marketing Site - Competitor Comparison Pages

This is a complete Next.js 14 implementation of Upstream's competitor comparison pages, ready to deploy.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd marketing-site
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the site.

### 3. Build for Production

```bash
npm run build
npm start
```

## 📁 Project Structure

```
marketing-site/
├── app/
│   ├── layout.tsx                    # Root layout with global styles
│   ├── page.tsx                      # Homepage
│   ├── competitors/
│   │   └── [slug]/
│   │       └── page.tsx              # Dynamic competitor comparison pages
│   └── alternatives/
│       └── [slug]/
│           └── page.tsx              # Dynamic alternative pages
├── components/
│   └── competitors/
│       ├── ComparisonTable.tsx       # Interactive comparison table
│       ├── PricingComparison.tsx     # Pricing calculator with savings
│       └── FeatureSpotlight.tsx      # Feature highlights
├── content/
│   └── competitors/
│       ├── data/
│       │   ├── types.ts              # TypeScript definitions
│       │   ├── adonis-intelligence.json
│       │   ├── upstream.json
│       │   └── comparison-framework.json
│       ├── vs-adonis.mdx             # Comparison page content
│       └── alternatives/
│           └── adonis.mdx            # Alternative page content
├── lib/
│   └── competitors.ts                # Data loading utilities
├── styles/
│   └── globals.css                   # Global Tailwind styles
├── public/
│   └── og-images/                    # Open Graph images (to be created)
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🎯 Available Routes

Once running, these pages will be available:

- `/` - Homepage with links to comparison pages
- `/competitors/vs-adonis` - Upstream vs. Adonis Intelligence comparison
- `/alternatives/adonis` - Adonis Intelligence alternative page

## 📝 Content Management

### Adding a New Competitor

1. **Create competitor data file:**
   ```bash
   cp content/competitors/data/adonis-intelligence.json content/competitors/data/waystar.json
   ```
   Edit `waystar.json` with Waystar's information.

2. **Create comparison page:**
   ```bash
   cp content/competitors/vs-adonis.mdx content/competitors/vs-waystar.mdx
   ```
   Update content for Waystar comparison.

3. **Create alternative page:**
   ```bash
   cp content/competitors/alternatives/adonis.mdx content/competitors/alternatives/waystar.mdx
   ```
   Update content for Waystar alternative.

4. **The routes are automatically created!**
   - `/competitors/vs-waystar`
   - `/alternatives/waystar`

### Updating Competitor Data

All competitor data is centralized in `/content/competitors/data/`:

- Edit `adonis-intelligence.json` to update Adonis pricing, features, etc.
- Changes propagate to all pages using that data automatically

### Updating Content

MDX files in `/content/competitors/` can be edited directly:

- `vs-adonis.mdx` - Full comparison page
- `alternatives/adonis.mdx` - Alternative page

Changes are hot-reloaded in development mode.

## 🎨 Customization

### Branding

Update colors in `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      primary: '#10b981',  // Green for Upstream
      secondary: '#3b82f6', // Blue accents
    },
  },
},
```

### Header & Footer

Edit the header/footer in:
- `/app/competitors/[slug]/page.tsx`
- `/app/alternatives/[slug]/page.tsx`

### Components

All React components are in `/components/competitors/`:

- `ComparisonTable.tsx` - Modify table structure, styling
- `PricingComparison.tsx` - Adjust pricing calculator logic
- `FeatureSpotlight.tsx` - Change feature highlight design

## 📊 Analytics Setup

### Google Analytics

Add to `/app/layout.tsx`:

```typescript
import Script from 'next/script';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX" />
        <Script id="google-analytics">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-XXXXXXXXXX');
          `}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  );
}
```

## 🔍 SEO Configuration

### Meta Tags

Meta tags are automatically generated from MDX frontmatter:

```yaml
---
title: "Upstream vs. Adonis Intelligence"
description: "Compare Upstream's early-warning..."
keywords: ["Upstream vs Adonis", "Adonis alternative"]
canonicalUrl: "https://upstream.com/competitors/vs-adonis"
ogImage: "/og-images/vs-adonis.png"
---
```

### Open Graph Images

Create images at `1200x630px` and place in `/public/og-images/`:

- `vs-adonis.png`
- `adonis-alternative.png`
- `default-comparison.png`

### Sitemap

Add to `/app/sitemap.ts`:

```typescript
import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://upstream.com',
      lastModified: new Date(),
      changeFrequency: 'yearly',
      priority: 1,
    },
    {
      url: 'https://upstream.com/competitors/vs-adonis',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: 'https://upstream.com/alternatives/adonis',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
  ];
}
```

## 🚀 Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Docker

```bash
docker build -t upstream-marketing .
docker run -p 3000:3000 upstream-marketing
```

### Static Export

```bash
# Add to next.config.js:
# output: 'export'

npm run build
# Files in /out directory
```

## ⚠️ Before Deploying

### Required Actions

1. **Fill in [NEEDS DATA] placeholders:**
   - Search for `[NEEDS DATA]` in MDX files
   - Add real customer testimonials, pricing, metrics

2. **Create Open Graph images:**
   - `/public/og-images/vs-adonis.png`
   - `/public/og-images/adonis-alternative.png`

3. **Update contact information:**
   - Replace `sales@upstream.com` with real email
   - Add phone number if available

4. **Verify competitor data:**
   - Check Adonis pricing is current
   - Verify feature claims are accurate

### Optional Enhancements

5. **Add remaining components:**
   - `MigrationTimeline.tsx`
   - `CTASection.tsx`
   - `SocialProof.tsx`

6. **Set up form handlers:**
   - "Schedule Demo" button action
   - Lead capture forms

7. **Configure analytics:**
   - Google Analytics
   - Google Search Console

## 📈 Monitoring

### Key Metrics to Track

- **SEO Rankings:**
  - "Upstream vs Adonis"
  - "Adonis alternative"

- **Traffic:**
  - Page views
  - Bounce rate
  - Time on page

- **Conversions:**
  - Demo requests
  - Form submissions

### Google Search Console

1. Verify ownership of domain
2. Submit sitemap: `https://upstream.com/sitemap.xml`
3. Monitor indexing status
4. Track search queries

## 🐛 Troubleshooting

### Build Errors

**Error:** `Cannot find module 'gray-matter'`
```bash
npm install gray-matter
```

**Error:** `@tailwindcss/typography not found`
```bash
npm install -D @tailwindcss/typography
```

### Component Errors

**Error:** `lucide-react icons not rendering`
```bash
npm install lucide-react
```

### Data Loading Errors

**Error:** `ENOENT: no such file or directory`
- Check that files exist in `/content/competitors/data/`
- Verify file names match (e.g., `adonis-intelligence.json` not `adonis.json`)

## 📚 Additional Documentation

- **Implementation guide:** `/docs/competitors/README.md`
- **Business case:** `/docs/competitors/EXECUTIVE-SUMMARY.md`
- **Deployment checklist:** `/docs/competitors/DEPLOYMENT-READY.md`
- **Sales resources:** `/docs/competitors/sales/battle-card-adonis.md`

## 🤝 Support

For questions:
- **Technical:** Review `/docs/competitors/IMPLEMENTATION-COMPLETE.md`
- **Content:** See `/docs/competitors/README.md`
- **Sales:** Use `/docs/competitors/sales/battle-card-adonis.md`

---

**You're ready to deploy! 🚀**

Start with:
```bash
npm install
npm run dev
```

Then visit [http://localhost:3000](http://localhost:3000) to see your competitor pages live!

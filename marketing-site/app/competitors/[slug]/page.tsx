import { getCompetitorData, getComparisonContent, getAllComparisonPages } from '@/lib/competitors';
import ComparisonTable from '@/components/competitors/ComparisonTable';
import PricingComparison from '@/components/competitors/PricingComparison';
import FeatureSpotlight from '@/components/competitors/FeatureSpotlight';
import { MDXRemote } from 'next-mdx-remote/rsc';

export async function generateStaticParams() {
  const pages = getAllComparisonPages();
  return pages.map((slug) => ({
    slug,
  }));
}

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const content = await getComparisonContent(params.slug);

  return {
    title: content.title || 'Competitor Comparison',
    description: content.description || '',
    keywords: content.keywords || [],
    openGraph: {
      title: content.title || 'Competitor Comparison',
      description: content.description || '',
      images: [content.ogImage || '/og-images/default-comparison.png'],
      type: 'article',
    },
    alternates: {
      canonical: content.canonicalUrl || `https://upstream.cx/competitors/${params.slug}`,
    },
  };
}

export default async function CompetitorPage({ params }: { params: { slug: string } }) {
  const content = await getComparisonContent(params.slug);
  const competitorSlug = params.slug.replace('vs-', '');
  const competitorData = await getCompetitorData(competitorSlug + '-intelligence');
  const upstreamData = await getCompetitorData('upstream');
  const framework = await getCompetitorData('comparison-framework');

  // Example feature highlights for FeatureSpotlight
  const featureHighlights = [
    {
      title: "Implementation Speed",
      description: "Time from contract to go-live",
      upstreamValue: "30 days - EHR-independent deployment",
      competitorValue: "3-6 months - requires EHR integration",
      winner: "upstream" as const,
      icon: "speed" as const,
    },
    {
      title: "Specialty Focus",
      description: "Vertical-specific intelligence",
      upstreamValue: "Built for dialysis, ABA, imaging, home health",
      competitorValue: "General specialty practices",
      winner: "upstream" as const,
      icon: "focus" as const,
    },
    {
      title: "Pricing Transparency",
      description: "Budgeting predictability",
      upstreamValue: "Fixed monthly subscription - transparent",
      competitorValue: "Percentage of recovery - not disclosed",
      winner: "upstream" as const,
      icon: "pricing" as const,
    },
    {
      title: "Prevention vs. Recovery",
      description: "When alerts fire",
      upstreamValue: "Early-warning 2-4 weeks before denials",
      competitorValue: "Real-time 24-48 hours after submission",
      winner: "upstream" as const,
      icon: "prevention" as const,
    },
  ];

  // Custom MDX components
  const components = {
    ComparisonTable: () => (
      <ComparisonTable
        upstream={upstreamData}
        competitor={competitorData}
        categories={framework.comparisonCategories}
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
    FeatureSpotlight: () => (
      <FeatureSpotlight
        features={featureHighlights}
        upstreamName="Upstream"
        competitorName={competitorData.company.name}
      />
    ),
    // Add proper table rendering
    table: (props: any) => (
      <div className="overflow-x-auto my-8">
        <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
      </div>
    ),
    thead: (props: any) => <thead className="bg-gray-50" {...props} />,
    tbody: (props: any) => <tbody className="divide-y divide-gray-200 bg-white" {...props} />,
    tr: (props: any) => <tr {...props} />,
    th: (props: any) => (
      <th
        className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-r border-gray-300 last:border-r-0"
        {...props}
      />
    ),
    td: (props: any) => (
      <td
        className="px-4 py-4 text-sm text-gray-700 border-r border-gray-300 last:border-r-0"
        {...props}
      />
    ),
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-gray-900">
              Upstream
            </a>
            <nav className="flex gap-6 text-sm">
              <a href="/competitors/vs-adonis" className="text-gray-600 hover:text-gray-900">
                Comparisons
              </a>
              <a
                href="#"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Schedule Demo
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <article className="prose prose-lg max-w-none">
          <MDXRemote source={content.body} components={components} />
        </article>

        {/* CTA Section */}
        <div className="mt-16 p-8 bg-green-50 border-2 border-green-500 rounded-lg">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            See Upstream in Action
          </h2>
          <p className="text-gray-700 mb-6">
            Schedule a demo to see how early-warning payer intelligence works for your specialty
            (dialysis, ABA, imaging, or home health).
          </p>
          <div className="flex gap-4">
            <a
              href="#"
              className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
            >
              Schedule Demo
            </a>
            <a
              href="/alternatives/adonis"
              className="px-6 py-3 border-2 border-green-600 text-green-700 rounded-lg font-semibold hover:bg-green-50 transition-colors"
            >
              Learn More
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-16 py-8 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 text-sm text-gray-600">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Upstream</h3>
              <p>Early-warning payer risk intelligence</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Comparisons</h3>
              <ul className="space-y-1">
                <li>
                  <a href="/competitors/vs-adonis" className="hover:text-gray-900">
                    Upstream vs. Adonis
                  </a>
                </li>
                <li>
                  <a href="/alternatives/adonis" className="hover:text-gray-900">
                    Adonis Alternative
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Contact</h3>
              <p>sales@upstream.cx</p>
              <p className="text-xs mt-4">© 2026 Upstream. All rights reserved.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

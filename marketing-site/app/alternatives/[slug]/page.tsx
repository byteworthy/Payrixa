import { getCompetitorData, getComparisonContent, getAllAlternativePages } from '@/lib/competitors';
import { MDXRemote } from 'next-mdx-remote/rsc';

export async function generateStaticParams() {
  const pages = getAllAlternativePages();
  return pages.map((slug) => ({
    slug,
  }));
}

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const content = await getComparisonContent(`alternatives/${params.slug}`);

  return {
    title: content.title || 'Competitor Alternative',
    description: content.description || '',
    keywords: content.keywords || [],
    openGraph: {
      title: content.title || 'Competitor Alternative',
      description: content.description || '',
      images: [content.ogImage || '/og-images/default-alternative.png'],
      type: 'article',
    },
    alternates: {
      canonical: content.canonicalUrl || `https://upstream.cx/alternatives/${params.slug}`,
    },
  };
}

export default async function AlternativePage({ params }: { params: { slug: string } }) {
  const content = await getComparisonContent(`alternatives/${params.slug}`);

  // Custom MDX components for proper table rendering
  const components = {
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
        <div className="mt-16 p-8 bg-blue-50 border-2 border-blue-500 rounded-lg">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Ready to Switch to Upstream?
          </h2>
          <p className="text-gray-700 mb-6">
            See how Upstream's early-warning intelligence and specialty-specific rules can work
            for your practice. Implementation takes just 30 days.
          </p>
          <div className="flex gap-4">
            <a
              href="#"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Get Started
            </a>
            <a
              href={`/competitors/vs-${params.slug}`}
              className="px-6 py-3 border-2 border-blue-600 text-blue-700 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
            >
              See Full Comparison
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

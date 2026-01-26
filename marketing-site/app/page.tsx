import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">
          Upstream - Early-Warning Payer Risk Intelligence
        </h1>

        <p className="text-lg text-gray-700 mb-8">
          Know what's changing in payer behavior before it costs you.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          <Link
            href="/competitors/vs-adonis"
            className="block p-6 border-2 border-green-500 rounded-lg hover:bg-green-50 transition-colors"
          >
            <h2 className="text-xl font-bold mb-2">Upstream vs. Adonis Intelligence</h2>
            <p className="text-gray-600">
              Compare early-warning prevention to real-time alerts. See features, pricing, and
              implementation timelines.
            </p>
          </Link>

          <Link
            href="/alternatives/adonis"
            className="block p-6 border-2 border-blue-500 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <h2 className="text-xl font-bold mb-2">Adonis Intelligence Alternative</h2>
            <p className="text-gray-600">
              Looking to switch? See how Upstream provides specialty-specific intelligence for
              dialysis, ABA, imaging, and home health.
            </p>
          </Link>
        </div>

        <div className="mt-12 p-6 bg-gray-100 rounded-lg">
          <h3 className="text-xl font-bold mb-4">Why Upstream?</h3>
          <ul className="space-y-2 text-gray-700">
            <li>✓ Early-warning detection 2-4 weeks before denials appear</li>
            <li>✓ Specialty-specific rules for dialysis, ABA, imaging, home health</li>
            <li>✓ 30-day implementation (EHR-independent)</li>
            <li>✓ Transparent fixed monthly pricing</li>
          </ul>
        </div>
      </div>
    </main>
  );
}

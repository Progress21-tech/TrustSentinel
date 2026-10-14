import Head from "next/head";
import Link from "next/link";
import { useState } from "react";
import { ArrowDownRight, ArrowRight, ArrowUpRight, Check, Menu, X } from "lucide-react";

const rawContactDestination = process.env.NEXT_PUBLIC_DESIGN_PARTNER_URL?.trim() ?? "";
const contactDestination = (() => {
  try {
    const parsed = new URL(rawContactDestination);
    return parsed.protocol === "https:" || parsed.protocol === "mailto:" ? rawContactDestination : "";
  } catch {
    return "";
  }
})();

const navigation = [
  ["Approach", "#how-it-works"],
  ["Capabilities", "#capabilities"],
  ["Integration", "#integration"],
  ["Responsible use", "#responsible-use"],
] as const;

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
  const ctaHref = contactDestination || "#contact";

  return (
    <>
      <Head>
        <title>Cerviqon | See risk in context</title>
        <meta name="description" content="Explainable transaction-risk assessment and beneficiary context for Nigerian financial institutions. Advisory, auditable, and designed to fit existing investigation workflows." />
        <meta property="og:title" content="Cerviqon — See risk in context" />
        <meta property="og:description" content="Transaction-risk intelligence with context, evidence, and institution-led decisions." />
        <meta property="og:type" content="website" />
        <meta property="og:locale" content="en_NG" />
        <meta name="theme-color" content="#E9EFE7" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className="landing-page">
        <a className="landing-skip-link" href="#main-content">Skip to content</a>
        <header className="landing-header">
          <div className="landing-header-inner">
            <Link className="landing-wordmark" href="/" aria-label="Cerviqon home">CERVIQON<span aria-hidden="true">.</span></Link>
            <nav className={menuOpen ? "landing-nav landing-nav-open" : "landing-nav"} aria-label="Main navigation">
              {navigation.map(([label, href]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}</a>)}
              <Link className="landing-app-link" href="/login">Analyst sign in <ArrowUpRight size={14} aria-hidden="true" /></Link>
            </nav>
            <a className="landing-header-cta" href={ctaHref}>{contactDestination ? "Talk with us" : "Discuss an evaluation"}<ArrowRight size={15} aria-hidden="true" /></a>
            <button className="landing-menu-toggle" type="button" aria-label={menuOpen ? "Close navigation" : "Open navigation"} aria-expanded={menuOpen} aria-controls="landing-mobile-navigation" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
          <nav id="landing-mobile-navigation" className={menuOpen ? "landing-mobile-nav landing-mobile-nav-open" : "landing-mobile-nav"} aria-label="Mobile navigation" aria-hidden={!menuOpen}>
            {navigation.map(([label, href]) => <a key={href} href={href} tabIndex={menuOpen ? 0 : -1} onClick={() => setMenuOpen(false)}>{label}</a>)}
            <Link href="/login" tabIndex={menuOpen ? 0 : -1} onClick={() => setMenuOpen(false)}>Analyst sign in</Link>
          </nav>
        </header>

        <main id="main-content">
          <section className="landing-hero">
            <div className="landing-hero-inner">
              <div className="landing-hero-copy">
                <p className="landing-eyebrow"><span />TRANSACTION RISK INTELLIGENCE</p>
                <h1>Make the transaction <em>make sense.</em></h1>
                <p className="landing-hero-line">See risk in context.</p>
                <p className="landing-hero-description">Cerviqon brings available transaction history and explainable signals into a clear assessment—so financial teams can review activity with more context.</p>
                <div className="landing-hero-actions">
                  <a className="landing-button landing-button-primary" href={ctaHref}>Discuss a design-partner evaluation <ArrowRight size={17} aria-hidden="true" /></a>
                  <a className="landing-text-link" href="#how-it-works">Explore the approach <ArrowDownRight size={16} aria-hidden="true" /></a>
                </div>
                <p className="landing-hero-note">Advisory decision support. Your institution remains in control.</p>
              </div>
              <div className="landing-visual-wrap" aria-label="Illustration of transaction context becoming an explainable assessment" role="img">
                <div className="landing-orbit landing-orbit-one" />
                <div className="landing-orbit landing-orbit-two" />
                <div className="landing-visual-label">CONTEXT TO EVIDENCE</div>
                <div className="landing-flow-card landing-flow-input">
                  <span className="landing-flow-index">01</span><span className="landing-flow-title">Transaction</span><span className="landing-flow-detail">Authorised event data</span>
                </div>
                <div className="landing-flow-connector"><span /></div>
                <div className="landing-flow-card landing-flow-middle">
                  <span className="landing-flow-index">02</span><span className="landing-flow-title">Available context</span><span className="landing-flow-detail">History · rules · model signals</span>
                </div>
                <div className="landing-flow-connector"><span /></div>
                <div className="landing-flow-card landing-flow-output">
                  <span className="landing-flow-index">03</span><span className="landing-flow-title">Assessment + evidence</span><span className="landing-flow-detail">For institution-led review</span><Check className="landing-flow-check" size={17} aria-hidden="true" />
                </div>
                <p className="landing-visual-caption">A product-flow illustration. No customer or live transaction data shown.</p>
              </div>
            </div>
            <div className="landing-hero-bottom"><span>BUILT FOR FINANCIAL INSTITUTIONS</span><span>EXPLAINABLE BY DESIGN</span><span>HUMAN-LED DECISIONS</span></div>
          </section>

          <section className="landing-section landing-problem" id="why-context-matters">
            <div className="landing-section-inner landing-problem-grid">
              <div>
                <p className="landing-eyebrow">THE OPERATING CHALLENGE</p>
                <h2>A signal on its own rarely tells the whole story.</h2>
              </div>
              <div className="landing-problem-copy">
                <p>A new beneficiary may be routine. A large transfer may be legitimate. The value of a signal depends on what is known about the account, the event, and the activity around it.</p>
                <p>Investigation teams need evidence they can examine—not a score presented as a verdict.</p>
                <a className="landing-inline-link" href="#how-it-works">How Cerviqon uses context <ArrowRight size={15} aria-hidden="true" /></a>
              </div>
            </div>
            <aside className="landing-research-note" aria-label="Research context">
              <span className="landing-research-mark" aria-hidden="true">₦</span>
              <p><strong>Context changes over time.</strong> A 2026 working paper reports that NIBSS figures showed ₦25.85 billion in Nigerian electronic-payment fraud losses in 2025, 51% lower than in 2024. The decline is progress; it is not evidence of Cerviqon’s effectiveness.</p>
              <a href="https://ir.nilds.gov.ng/handle/123456789/3473" target="_blank" rel="noreferrer">Read the source and period notes <ArrowUpRight size={13} aria-hidden="true" /></a>
            </aside>
          </section>

          <section className="landing-section landing-how" id="how-it-works">
            <div className="landing-section-inner">
              <div className="landing-section-heading">
                <p className="landing-eyebrow">HOW IT WORKS</p>
                <h2>From event data to reviewable evidence.</h2>
                <p>The same scoring service supports the analyst workspace and institution API.</p>
              </div>
              <div className="landing-steps">
                <article className="landing-step"><span className="landing-step-number">01</span><h3>Send a transaction</h3><p>An authorised client submits supported transaction fields using pseudonymous references and its institution credential.</p></article>
                <article className="landing-step"><span className="landing-step-number">02</span><h3>Assess in context</h3><p>The shared service evaluates supported rules, available account history, and the configured model. Missing history is identified as cold start.</p></article>
                <article className="landing-step"><span className="landing-step-number">03</span><h3>Review the evidence</h3><p>Cerviqon returns an advisory score, band, recommendation, reason codes, completeness, and assessment version details.</p></article>
                <article className="landing-step"><span className="landing-step-number">04</span><h3>Keep decisions yours</h3><p>Your institution decides what to do next. Analysts can record investigation outcomes for audit; they are not fed into training automatically.</p></article>
              </div>
              <p className="landing-advisory-note"><span aria-hidden="true">i</span> Cerviqon does not authorise, block, or reverse a payment.</p>
            </div>
          </section>

          <section className="landing-section landing-capabilities" id="capabilities">
            <div className="landing-section-inner">
              <div className="landing-section-heading landing-section-heading-row">
                <div><p className="landing-eyebrow">CURRENT CAPABILITIES</p><h2>Useful context, clearly explained.</h2></div>
                <p>Describes the current prototype. Institutional deployment and operating controls require evaluation.</p>
              </div>
              <div className="landing-capability-grid">
                <article className="landing-capability"><span className="landing-capability-icon"><span>01</span></span><h3>Signals with a source</h3><p>Assessments return reason codes linked to the rules or model evidence used by the scoring service.</p></article>
                <article className="landing-capability"><span className="landing-capability-icon"><span>02</span></span><h3>Beneficiary context</h3><p>Where authorised account history is available, the service can consider observed beneficiary familiarity and relevant transaction patterns.</p></article>
                <article className="landing-capability"><span className="landing-capability-icon"><span>03</span></span><h3>Explicit cold starts</h3><p>Limited or missing history is identified in the result. A first-time beneficiary alone is not treated as proof of fraud.</p></article>
                <article className="landing-capability"><span className="landing-capability-icon"><span>04</span></span><h3>Traceable assessments</h3><p>Assessment IDs, request IDs, decision evidence, and model, policy, and feature-schema versions support review.</p></article>
              </div>
            </div>
          </section>

          <section className="landing-integration" id="integration">
            <div className="landing-section-inner landing-integration-grid">
              <div className="landing-integration-copy">
                <p className="landing-eyebrow">INTEGRATION APPROACH</p>
                <h2>Designed to sit alongside the systems you already operate.</h2>
                <p>A versioned API lets an institution-controlled backend request an assessment and receive a structured response. Evaluation can be planned around synthetic data, authorised history, or a controlled shadow-mode exercise led by the institution.</p>
                <p>The current service does not run an institution-wide shadow deployment by itself. No bank or payment-provider integration is represented as live.</p>
                <a className="landing-button landing-button-light" href={ctaHref}>Discuss an evaluation <ArrowRight size={16} aria-hidden="true" /></a>
              </div>
              <div className="landing-api-card" aria-label="Example API request details">
                <div className="landing-api-card-top"><span>INSTITUTION BACKEND</span><span className="landing-api-status"><i /> API v1</span></div>
                <div className="landing-api-line"><span className="landing-api-method">POST</span><code>/v1/risk/score</code></div>
                <div className="landing-api-divider" />
                <p>Structured assessment response</p>
                <div className="landing-api-fields"><span>risk_score</span><span>reason_codes</span><span>data_completeness</span><span>assessment_id</span><span>model + policy versions</span></div>
                <div className="landing-api-foot"><span>INSTITUTION-SCOPED ACCESS</span><span>ADVISORY ONLY</span></div>
              </div>
            </div>
          </section>

          <section className="landing-section landing-trust" id="responsible-use">
            <div className="landing-section-inner landing-trust-grid">
              <div className="landing-section-heading"><p className="landing-eyebrow">RESPONSIBLE USE</p><h2>Built to support a decision, not make it for you.</h2><p>Financial institutions set the controls, authorised data, and actions around their evaluation.</p></div>
              <div className="landing-trust-list">
                <article><span>01</span><div><h3>Institution-scoped data</h3><p>Configured credentials scope application records to an institution. Cross-institution data pooling is not part of the current design.</p></div></article>
                <article><span>02</span><div><h3>Data minimisation</h3><p>Use pseudonymous references and submit only the supported context needed for the agreed assessment.</p></div></article>
                <article><span>03</span><div><h3>Human review</h3><p>Risk bands and recommendations are advisory. Your institution retains control of customer and payment decisions.</p></div></article>
                <article><span>04</span><div><h3>Evaluation before reliance</h3><p>The current model evaluation is synthetic. Hosting, retention, key-management, and other operational controls need institution-specific verification.</p></div></article>
              </div>
            </div>
          </section>

          <section className="landing-contact" id="contact">
            <div className="landing-section-inner landing-contact-inner">
              <div><p className="landing-eyebrow">DESIGN-PARTNER EVALUATION</p><h2>Start with the problem your team needs to understand.</h2><p>Discuss an evaluation scope, the context your institution can authorise, and the controls needed before a pilot.</p></div>
              <div className="landing-contact-action">
                {contactDestination ? <a className="landing-button landing-button-primary" href={contactDestination}>Discuss an evaluation <ArrowUpRight size={16} aria-hidden="true" /></a> : <p className="landing-contact-pending">A contact destination is not configured. Set NEXT_PUBLIC_DESIGN_PARTNER_URL to a monitored HTTPS or mailto destination before launch.</p>}
                <Link className="landing-inline-link" href="/login">Analyst workspace <ArrowRight size={14} aria-hidden="true" /></Link>
              </div>
            </div>
          </section>
        </main>

        <footer className="landing-footer">
          <div className="landing-section-inner landing-footer-main">
            <div className="landing-footer-brand"><Link className="landing-wordmark" href="/">CERVIQON<span>.</span></Link><p>See risk in context.</p><small>Advisory transaction-risk intelligence for institution-led review.</small></div>
            <div className="landing-footer-column"><strong>Explore</strong>{navigation.map(([label, href]) => <a key={href} href={href}>{label}</a>)}</div>
            <div className="landing-footer-column"><strong>Workspace</strong><Link href="/login">Analyst sign in</Link><a href="#integration">API approach</a><a href="#contact">Design-partner evaluation</a></div>
            <div className="landing-footer-column"><strong>Trust</strong><a href="#responsible-use">Responsible use</a><span>Privacy and legal information pending publication</span></div>
          </div>
          <div className="landing-footer-bottom"><span>© {new Date().getFullYear()} Cerviqon</span><span>Prototype for evaluation. Not a payment decision service.</span></div>
        </footer>
      </div>
    </>
  );
}

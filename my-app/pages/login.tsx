import { FormEvent, useState } from "react";
import { useRouter } from "next/router";
import { ArrowRight, LockKeyhole, ShieldCheck } from "lucide-react";
import { login } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      await login(email, password);
      await router.replace("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in.");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-aside" aria-label="TrustSentinel overview">
        <div className="brand-lockup"><span className="brand-mark"><ShieldCheck size={23} /></span><span><strong>TrustSentinel</strong><small>INNOVATEX · RISK INTELLIGENCE</small></span></div>
        <div className="login-message">
          <span className="eyebrow">FINANCIAL RISK OPERATIONS</span>
          <h1>See the signals.<br />Protect the trust.</h1>
          <p>Contextual risk decisions for payments, investigations, and customer protection.</p>
        </div>
        <div className="login-footnote">SYNTHETIC PROTOTYPE · ANALYST ACCESS</div>
      </section>
      <section className="login-panel">
        <div className="login-form-wrap">
          <div className="login-heading"><span className="login-icon"><LockKeyhole size={19} /></span><span className="eyebrow">SECURE WORKSPACE</span></div>
          <h2>Sign in</h2>
          <p className="muted-copy">Use your TrustSentinel analyst credentials.</p>
          <form onSubmit={submit} className="login-form">
            <label htmlFor="email">Work email</label>
            <input id="email" name="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            {router.query.reason === "expired" && <p className="form-error" role="status">Your session expired. Sign in again to continue.</p>}
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="primary-button login-submit" type="submit" disabled={pending}>
              {pending ? "Verifying credentials…" : <>Continue <ArrowRight size={17} /></>}
            </button>
          </form>
          <p className="login-security">Credentials are verified by the TrustSentinel API. Your session is held only for this browser session.</p>
        </div>
      </section>
    </main>
  );
}

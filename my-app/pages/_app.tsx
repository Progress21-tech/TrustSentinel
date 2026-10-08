import "@/styles/globals.css";
import { useEffect, useState } from "react";
import type { AppProps } from "next/app";
import { useRouter } from "next/router";
import { clearSession, getSession, hasSession } from "@/lib/api";

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [state, setState] = useState<"checking" | "signed-in" | "signed-out">("checking");
  const isLogin = router.pathname === "/login";
  const isProtected = router.pathname.startsWith("/dashboard");

  useEffect(() => {
    let current = true;
    const sessionWasPresent = hasSession();
    const expired = () => {
      clearSession();
      setState("signed-out");
      void router.replace("/login?reason=expired");
    };
    const loggedOut = () => setState("signed-out");
    window.addEventListener("trustsentinel:session-expired", expired);
    window.addEventListener("trustsentinel:logout", loggedOut);

    if (isProtected && !sessionWasPresent) {
      void router.replace("/login");
    } else if ((isProtected || isLogin) && sessionWasPresent) {
      getSession().then(
        () => {
          if (!current) return;
          setState("signed-in");
          if (isLogin) void router.replace("/dashboard");
        },
        () => {
          if (!current) return;
          setState("signed-out");
          if (isProtected) void router.replace(sessionWasPresent ? "/login?reason=expired" : "/login");
        },
      );
    }

    return () => {
      current = false;
      window.removeEventListener("trustsentinel:session-expired", expired);
      window.removeEventListener("trustsentinel:logout", loggedOut);
    };
  }, [isLogin, isProtected, router]);

  if (isProtected && state !== "signed-in") {
    return <main className="auth-loading" aria-live="polite">Verifying analyst session…</main>;
  }
  if (isLogin && state === "signed-in") return <main className="auth-loading">Opening workspace…</main>;
  return <Component {...pageProps} />;
}

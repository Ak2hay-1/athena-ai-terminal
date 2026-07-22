"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DisclaimerModal } from "@/components/legal/disclaimer-modal";
import { DISCLAIMER_VERSION } from "@/constants/disclaimer";
import { acceptDisclaimer, getDisclaimerStatus } from "@/services/disclaimer";
import { useAuthStore } from "@/store/auth-store";
import packageJson from "../../../package.json";

type GateState = "loading" | "required" | "accepted";

export function DisclaimerGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const [state, setState] = useState<GateState>("loading");
  const [accepting, setAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    if (!user) {
      setState("loading");
      return;
    }

    setState("loading");
    setError(null);

    try {
      const status = await getDisclaimerStatus();
      const accepted =
        status.accepted &&
        status.disclaimer_version === DISCLAIMER_VERSION &&
        status.required_version === DISCLAIMER_VERSION;

      setState(accepted ? "accepted" : "required");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to verify disclaimer status.",
      );
      // Still show the modal so the user can accept (or decline) explicitly.
      setState("required");
    }
  }, [user]);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const handleAccept = async () => {
    setAccepting(true);
    setError(null);

    try {
      const status = await acceptDisclaimer({
        app_version: packageJson.version,
        disclaimer_version: DISCLAIMER_VERSION,
      });

      if (!status.accepted || status.disclaimer_version !== DISCLAIMER_VERSION) {
        throw new Error("Disclaimer acceptance was not recorded. Please try again.");
      }

      setState("accepted");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to save disclaimer acceptance.",
      );
      setState("required");
    } finally {
      setAccepting(false);
    }
  };

  const handleDecline = () => {
    logout();
    router.replace("/login");
  };

  if (state === "accepted") {
    return <>{children}</>;
  }

  if (state === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">
        Checking risk disclaimer…
      </div>
    );
  }

  return (
    <>
      <div className="flex min-h-screen items-center justify-center bg-background px-4 text-center text-sm text-muted">
        Please review and accept the risk disclaimer to continue.
      </div>
      <DisclaimerModal
        open
        accepting={accepting}
        error={error}
        onAccept={() => {
          void handleAccept();
        }}
        onDecline={handleDecline}
      />
    </>
  );
}

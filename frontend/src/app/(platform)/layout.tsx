import { AuthGate } from "@/components/auth/auth-gate";
import { DisclaimerGate } from "@/components/auth/disclaimer-gate";
import { PlatformChrome } from "@/components/layout/platform-chrome";

export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGate>
      <DisclaimerGate>
        <PlatformChrome>{children}</PlatformChrome>
      </DisclaimerGate>
    </AuthGate>
  );
}

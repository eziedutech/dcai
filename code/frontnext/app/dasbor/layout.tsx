import { Suspense } from "react";
import { DashShell } from "@/components/dash/shell";

// Every dashboard view depends on the signed-in guardian, so there is no shared static
// shell to validate for instant navigation (docs: authentication-with-cache-components).
export const instant = false;

export default function DashLayout({ children }: LayoutProps<"/dasbor">) {
  return (
    <Suspense>
      <DashShell>{children}</DashShell>
    </Suspense>
  );
}

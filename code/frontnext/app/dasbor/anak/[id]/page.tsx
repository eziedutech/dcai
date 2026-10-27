import { Suspense } from "react";
import { ChildRoute } from "@/components/dash/child-route";

// Per-guardian data only; nothing to prerender (see the dashboard layout).
export const instant = false;

export default function Page() {
  return (
    <Suspense>
      <ChildRoute />
    </Suspense>
  );
}

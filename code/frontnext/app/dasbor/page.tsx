import { DashHome } from "@/components/dash/home";

// Per-guardian data only; nothing to prerender (see the dashboard layout).
export const instant = false;

export default function Page() {
  return <DashHome />;
}

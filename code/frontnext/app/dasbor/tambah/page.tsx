import { Suspense } from "react";
import { AddChild } from "@/components/dash/add-child";

export const instant = false;

export default function Page() {
  return (
    <Suspense>
      <AddChild />
    </Suspense>
  );
}

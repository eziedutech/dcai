import { Suspense } from "react";
import { AddChild } from "@/components/dash/add-child";

export default function Page() {
  return (
    <Suspense>
      <AddChild />
    </Suspense>
  );
}

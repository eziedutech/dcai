"use client";

import { useParams } from "next/navigation";
import { ChildView } from "./child";

export function ChildRoute() {
  const { id } = useParams<{ id: string }>();
  return <ChildView key={id} childId={id} />;
}

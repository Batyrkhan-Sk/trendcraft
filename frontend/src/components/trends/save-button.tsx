"use client";

import { useState, useTransition } from "react";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { Button } from "@/components/ui/primitives";
import { apiBase } from "@/lib/api";

export function SaveButton({
  entityType,
  entityId,
  initiallySaved = false,
  size = "md",
}: {
  entityType: "trend" | "scenario" | "video";
  entityId: string;
  initiallySaved?: boolean;
  size?: "sm" | "md";
}) {
  const [saved, setSaved] = useState(initiallySaved);
  const [pending, startTransition] = useTransition();

  const toggle = () => {
    // Optimistic: the toggle is cheap and reverting on failure is less jarring
    // than a spinner on every bookmark.
    const next = !saved;
    setSaved(next);
    startTransition(async () => {
      try {
        const headers = {
          "Content-Type": "application/json",
          "X-User-Email": "demo@trendcraft.app",
        };
        if (next) {
          await fetch(`${apiBase()}/saved`, {
            method: "POST",
            headers,
            body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
          });
        } else {
          await fetch(`${apiBase()}/saved/${entityType}/${entityId}`, {
            method: "DELETE",
            headers,
          });
        }
      } catch {
        setSaved(!next);
      }
    });
  };

  return (
    <Button
      variant="secondary"
      size={size}
      onClick={toggle}
      disabled={pending}
      aria-pressed={saved}
      title={saved ? "Remove from saved" : "Save this"}
    >
      {saved ? (
        <>
          <BookmarkCheck className="size-4 text-[#a99bff]" /> Saved
        </>
      ) : (
        <>
          <Bookmark className="size-4" /> Save
        </>
      )}
    </Button>
  );
}

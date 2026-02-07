"use client";

import { LoaderCircle } from "lucide-react";
import { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type HoverBorderButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  isLoading?: boolean;
};

// Aceternity-style animated border button.
export function HoverBorderButton({
  className,
  children,
  isLoading = false,
  disabled,
  ...props
}: HoverBorderButtonProps) {
  const blocked = disabled || isLoading;

  return (
    <button
      type="button"
      className={cn(
        "group relative inline-flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl border border-cyan-200/40 px-5 py-3 text-sm font-semibold text-cyan-100 transition",
        "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.35),transparent_45%),radial-gradient(circle_at_80%_80%,rgba(74,222,128,0.25),transparent_45%)] before:opacity-0 before:transition group-hover:before:opacity-100",
        "after:absolute after:inset-[1px] after:rounded-2xl after:bg-slate-950/90",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      disabled={blocked}
      {...props}
    >
      <span className="relative z-10 inline-flex items-center gap-2">
        {isLoading ? (
          <>
            <LoaderCircle className="h-4 w-4 animate-spin" />
            Predicting...
          </>
        ) : (
          children
        )}
      </span>
    </button>
  );
}


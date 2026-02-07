"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

import { cn } from "@/lib/utils";

type BackgroundGradientProps = {
  children: ReactNode;
  className?: string;
  containerClassName?: string;
};

// Aceternity-style gradient container for cards / sections.
export function BackgroundGradient({
  children,
  className,
  containerClassName,
}: BackgroundGradientProps) {
  return (
    <div className={cn("group relative h-full w-full p-[1px]", containerClassName)}>
      <div
        className={cn(
          "absolute inset-0 rounded-3xl bg-[radial-gradient(circle_at_15%_15%,rgba(52,211,153,0.45),transparent_35%),radial-gradient(circle_at_80%_20%,rgba(56,189,248,0.4),transparent_45%),radial-gradient(circle_at_50%_90%,rgba(251,191,36,0.3),transparent_35%),linear-gradient(130deg,rgba(2,6,23,0.95),rgba(15,23,42,0.95))] opacity-90 blur-lg transition duration-300 group-hover:opacity-100",
        )}
      />
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className={cn(
          "relative h-full rounded-3xl border border-white/15 bg-slate-950/80 p-5 backdrop-blur-xl md:p-7",
          className,
        )}
      >
        {children}
      </motion.div>
    </div>
  );
}


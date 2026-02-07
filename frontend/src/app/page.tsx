"use client";

import { useRouter } from "next/navigation";

import { BackgroundGradient } from "@/components/aceternity/background-gradient";
import { HoverBorderButton } from "@/components/aceternity/hover-border-button";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl items-center px-4 py-10 md:px-8">
      <BackgroundGradient className="w-full space-y-5 text-center">
        <p className="inline-flex rounded-full border border-cyan-200/35 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-200">
          FleetAI
        </p>
        <h1 className="text-3xl font-semibold text-slate-100 md:text-5xl">
          Vehicle Maintenance Prediction System
        </h1>
        <p className="mx-auto max-w-2xl text-sm text-slate-300 md:text-base">
          Milestone-1 is focused on maintenance risk prediction with confidence
          and feature importance from manual input or CSV upload.
        </p>
        <div className="mx-auto w-full max-w-xs">
          <HoverBorderButton onClick={() => router.push("/predict")}>
            Go to Predict
          </HoverBorderButton>
        </div>
      </BackgroundGradient>
    </main>
  );
}

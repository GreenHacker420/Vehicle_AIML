"use client";

import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

import AnimatedContent from "@/components/AnimatedContent";
import FadeContent from "@/components/FadeContent";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { HoverBorderGradient } from "@/components/ui/hover-border-gradient";
import ShaderBackground from "@/components/ui/shader-background";
import { TextGenerateEffect } from "@/components/ui/text-generate-effect";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="relative w-screen min-h-screen overflow-hidden">
      <ShaderBackground />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_15%_20%,rgba(34,211,238,0.22),transparent_32%),radial-gradient(circle_at_80%_85%,rgba(249,115,22,0.18),transparent_34%),linear-gradient(170deg,rgba(2,6,23,0.75),rgba(15,23,42,0.72))]" />

      <div className="relative z-20 mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 md:px-8">
        <AnimatedContent distance={80} className="w-full">
          <Card className="border-white/25 bg-white/88 shadow-[0_30px_90px_rgba(2,6,23,0.38)] backdrop-blur-xl">
            <CardContent className="space-y-6 p-8 text-center md:p-14">
              <Badge className="mx-auto border-slate-300 bg-slate-100 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-700">
                FleetAI
              </Badge>

              <TextGenerateEffect
                words="Vehicle Maintenance Prediction System"
                className="mx-auto max-w-3xl text-center text-4xl leading-tight font-semibold tracking-tight md:text-6xl"
                duration={0.45}
              />

              <FadeContent blur duration={900} delay={250}>
                <p className="mx-auto max-w-2xl text-sm leading-7 text-slate-600 md:text-lg">
                  Upload CSV data or enter vehicle details manually to predict
                  maintenance risk, confidence score, and top contributing
                  factors.
                </p>
              </FadeContent>

              <FadeContent blur duration={900} delay={420}>
                <div className="mx-auto w-full max-w-sm">
                  <HoverBorderGradient
                    as="button"
                    containerClassName="w-full rounded-xl"
                    className="inline-flex w-full items-center justify-center gap-2 bg-slate-950 text-sm font-medium text-white md:text-base"
                    onClick={() => router.push("/predict")}
                  >
                    Open Predictor
                    <ArrowRight className="h-4 w-4" />
                  </HoverBorderGradient>
                </div>
              </FadeContent>
            </CardContent>
          </Card>
        </AnimatedContent>
      </div>
    </main>
  );
}

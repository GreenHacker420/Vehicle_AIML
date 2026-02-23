"use client";

import { useMutation } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  Copy,
  Download,
  FileJson,
  Gauge,
  Info,
  RotateCcw,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useMemo, useState } from "react";

import AnimatedContent from "@/components/AnimatedContent";
import FadeContent from "@/components/FadeContent";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { BackgroundGradient } from "@/components/ui/background-gradient";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileUpload } from "@/components/ui/file-upload";
import { HoverBorderGradient } from "@/components/ui/hover-border-gradient";
import { Input } from "@/components/ui/input";
import ShaderBackground from "@/components/ui/shader-background";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TextGenerateEffect } from "@/components/ui/text-generate-effect";
import { Textarea } from "@/components/ui/textarea";
import {
  predictFromCsvFile,
  predictFromManualInput,
} from "@/services/predictionService";
import type {
  InsightDriver,
  ManualPredictionInput,
  PredictionItem,
  PredictionResponse,
  RecommendationItem,
} from "@/types/prediction";
import { cn } from "@/lib/utils";

type ManualFormState = {
  mileage: string;
  engine_hours: string;
  fault_codes: string;
  service_history: string;
  usage_patterns: string;
};

const INITIAL_FORM: ManualFormState = {
  mileage: "",
  engine_hours: "",
  fault_codes: "",
  service_history: "",
  usage_patterns: "",
};

const RISK_BADGE_STYLES: Record<"LOW" | "MEDIUM" | "HIGH", string> = {
  LOW: "border-emerald-300 bg-emerald-50 text-emerald-700",
  MEDIUM: "border-amber-300 bg-amber-50 text-amber-700",
  HIGH: "border-rose-300 bg-rose-50 text-rose-700",
};

const DRIVER_BADGE_STYLES: Record<"RISK_UP" | "RISK_DOWN" | "NEUTRAL", string> = {
  RISK_UP: "border-rose-300 bg-rose-50 text-rose-700",
  RISK_DOWN: "border-emerald-300 bg-emerald-50 text-emerald-700",
  NEUTRAL: "border-slate-300 bg-slate-100 text-slate-700",
};

const PRIORITY_BADGE_STYLES: Record<"HIGH" | "MEDIUM" | "LOW", string> = {
  HIGH: "border-rose-300 bg-rose-50 text-rose-700",
  MEDIUM: "border-amber-300 bg-amber-50 text-amber-700",
  LOW: "border-emerald-300 bg-emerald-50 text-emerald-700",
};

export default function PredictPage() {
  const [manualForm, setManualForm] = useState<ManualFormState>(INITIAL_FORM);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const manualPrediction = useMutation({
    mutationFn: (payload: ManualPredictionInput) =>
      predictFromManualInput(payload),
    onSuccess: (response) => {
      setResult(response);
      setErrorMessage(null);
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    },
    onError: (error) => {
      setErrorMessage(error.message);
    },
  });

  const csvPrediction = useMutation({
    mutationFn: (file: File) => predictFromCsvFile(file),
    onSuccess: (response) => {
      setResult(response);
      setErrorMessage(null);
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    },
    onError: (error) => {
      setErrorMessage(error.message);
    },
  });

  const isLoading = manualPrediction.isPending || csvPrediction.isPending;

  const featureRows = useMemo(() => {
    if (!result?.feature_importance) {
      return [];
    }
    return Object.entries(result.feature_importance)
      .map(([feature, importance]) => ({
        feature,
        importance,
      }))
      .sort((a, b) => b.importance - a.importance);
  }, [result]);

  const batchRows: PredictionItem[] = useMemo(() => {
    if (!result?.predictions) {
      return [];
    }
    return result.predictions.slice(0, 8);
  }, [result]);

  const insightRows: InsightDriver[] = useMemo(() => {
    if (!result?.insight_drivers) {
      return [];
    }
    return result.insight_drivers.slice(0, 6);
  }, [result]);

  const recommendationRows: RecommendationItem[] = useMemo(() => {
    if (!result?.recommendations) {
      return [];
    }
    return result.recommendations.slice(0, 5);
  }, [result]);

  const confidenceLabel = result
    ? `${(result.confidence * 100).toFixed(2)}%`
    : "--";
  const probabilityLabel = result
    ? `${(result.risk_probability * 100).toFixed(2)}%`
    : "--";

  const handleInputChange = (key: keyof ManualFormState, value: string): void => {
    setManualForm((previous) => ({
      ...previous,
      [key]: value,
    }));
  };

  const resetError = () => {
    if (errorMessage) {
      setErrorMessage(null);
    }
  };

  const handleManualPredict = () => {
    if (manualPrediction.isPending || csvPrediction.isPending) {
      return;
    }
    resetError();

    const payload: ManualPredictionInput = {
      mileage: Number(manualForm.mileage),
      engine_hours: Number(manualForm.engine_hours),
      fault_codes: manualForm.fault_codes.trim(),
      service_history: manualForm.service_history.trim(),
      usage_patterns: manualForm.usage_patterns.trim(),
    };

    const hasInvalidValue =
      Number.isNaN(payload.mileage) ||
      Number.isNaN(payload.engine_hours) ||
      payload.fault_codes.length === 0 ||
      payload.service_history.length === 0 ||
      payload.usage_patterns.length === 0;

    if (hasInvalidValue) {
      setErrorMessage(
        "Please complete all manual input fields before predicting.",
      );
      return;
    }

    manualPrediction.mutate(payload);
  };

  const handleCsvPredict = () => {
    if (manualPrediction.isPending || csvPrediction.isPending) {
      return;
    }
    resetError();

    if (!csvFile) {
      setErrorMessage("Select a CSV file before running prediction.");
      return;
    }

    csvPrediction.mutate(csvFile);
  };

  const handleCsvChange = (files: File[]) => {
    const selected = files[0] ?? null;
    if (!selected) {
      return;
    }
    if (!selected.name.toLowerCase().endsWith(".csv")) {
      setErrorMessage("Please upload a valid .csv file.");
      setCsvFile(null);
      return;
    }
    setCsvFile(selected);
    setErrorMessage(null);
  };

  const handleCopySummary = () => {
    if (result?.insight_summary) {
      navigator.clipboard.writeText(result.insight_summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadCSVTemplate = () => {
    const csv = "mileage,engine_hours,fault_codes,service_history,usage_patterns\n64000,1200,P0171;P0420,average,mixed city driving\n85000,2500,P0300,poor,heavy commercial";
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vehicle_input_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClearForm = () => {
    setManualForm(INITIAL_FORM);
    setErrorMessage(null);
  };

  const exportResultAsJSON = () => {
    if (!result) return;
    const json = JSON.stringify(result, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `prediction_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Keyboard shortcut: Ctrl+Enter to predict
  useState(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleManualPredict();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  });

  return (
    <main className="relative w-screen min-h-screen overflow-x-hidden pb-16">
      <ShaderBackground />
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_12%_18%,rgba(14,165,233,0.2),transparent_30%),radial-gradient(circle_at_88%_80%,rgba(251,146,60,0.16),transparent_36%),linear-gradient(180deg,rgba(15,23,42,0.65),rgba(15,23,42,0.2)_36%,rgba(248,250,252,0.84)_68%,rgba(250,250,255,0.93)_100%)]" />

      <div className="relative z-20 mx-auto flex w-full max-w-[1800px] flex-col gap-6 px-4 pt-8 md:px-8 md:pt-10">
        <AnimatedContent distance={70}>
          <Card className="border-white/25 bg-white/82 shadow-[0_30px_80px_rgba(15,23,42,0.35)] backdrop-blur-xl">
            <CardContent className="space-y-4 p-6 text-center md:p-10">
              <Badge className="mx-auto w-fit border-slate-300 bg-slate-100 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-700">
                Predict
              </Badge>
              <TextGenerateEffect
                words="Maintenance Risk Intelligence"
                className="mx-auto max-w-4xl text-center text-3xl font-semibold leading-tight tracking-tight md:text-6xl"
                duration={0.4}
              />
              <FadeContent blur duration={900} delay={240}>
                <p className="mx-auto max-w-3xl text-sm text-slate-700 md:text-lg">
                  Analyze maintenance risk from manual entries or bulk CSV data
                  using a single advanced prediction workspace.
                </p>
              </FadeContent>
            </CardContent>
          </Card>
        </AnimatedContent>

        <section className="grid w-full gap-6 lg:grid-cols-2">
          <AnimatedContent distance={50} delay={0.05}>
            <BackgroundGradient className="rounded-2xl">
              <Card className="border-slate-200/90 bg-white/94 shadow-xl shadow-cyan-200/45">
                <CardHeader>
                  <CardTitle className="text-slate-900">Manual Input</CardTitle>
                  <CardDescription className="text-slate-600">
                    Required fields: mileage, engine hours, fault codes,
                    service history, usage patterns. Press Ctrl+Enter to predict.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input
                    type="number"
                    min={0}
                    placeholder="Mileage (e.g. 64000)"
                    value={manualForm.mileage}
                    onChange={(event) =>
                      handleInputChange("mileage", event.target.value)
                    }
                    className="focus:ring-2 focus:ring-cyan-500"
                  />
                  <Input
                    type="number"
                    min={0}
                    placeholder="Engine Hours (e.g. 1200)"
                    value={manualForm.engine_hours}
                    onChange={(event) =>
                      handleInputChange("engine_hours", event.target.value)
                    }
                    className="focus:ring-2 focus:ring-cyan-500"
                  />
                  <Textarea
                    placeholder="Fault Codes (e.g. P0171, P0420)"
                    value={manualForm.fault_codes}
                    onChange={(event) =>
                      handleInputChange("fault_codes", event.target.value)
                    }
                    className="min-h-24 border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-cyan-500"
                  />
                  <Input
                    placeholder="Service History (e.g. good, average, poor)"
                    value={manualForm.service_history}
                    onChange={(event) =>
                      handleInputChange("service_history", event.target.value)
                    }
                    className="focus:ring-2 focus:ring-cyan-500"
                  />
                  <Textarea
                    placeholder="Usage Patterns (mixed city driving, heavy commercial, etc.)"
                    value={manualForm.usage_patterns}
                    onChange={(event) =>
                      handleInputChange("usage_patterns", event.target.value)
                    }
                    className="min-h-24 border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-cyan-500"
                  />
                  <HoverBorderGradient
                    as="button"
                    containerClassName="w-full rounded-xl"
                    className={cn(
                      "w-full bg-slate-950 text-sm font-medium text-white",
                      isLoading && "opacity-70 cursor-not-allowed",
                    )}
                    onClick={handleManualPredict}
                    aria-disabled={isLoading}
                  >
                    {manualPrediction.isPending
                      ? "Predicting..."
                      : "Predict from manual input"}
                  </HoverBorderGradient>
                  <button
                    onClick={handleClearForm}
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                  >
                    <RotateCcw className="mr-2 inline h-4 w-4" />
                    Clear form
                  </button>
                </CardContent>
              </Card>
            </BackgroundGradient>
          </AnimatedContent>

          <AnimatedContent distance={50} delay={0.1}>
            <BackgroundGradient className="rounded-2xl">
              <Card className="border-slate-200/90 bg-white/94 shadow-xl shadow-orange-200/30">
                <CardHeader>
                  <CardTitle className="text-slate-900">CSV Upload</CardTitle>
                  <CardDescription className="text-slate-600">
                    Upload a CSV with required columns for batch prediction.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FileUpload onChange={handleCsvChange} />
                  <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="inline-flex items-center gap-1.5 font-medium">
                          <UploadCloud className="h-3.5 w-3.5" />
                          Required CSV columns
                        </p>
                        <p className="mt-1">
                          mileage, engine_hours, fault_codes, service_history,
                          usage_patterns
                        </p>
                        <p className="mt-1 truncate text-slate-600">
                          Selected: {csvFile?.name ?? "none"}
                        </p>
                      </div>
                      <button
                        onClick={downloadCSVTemplate}
                        className="flex-shrink-0 rounded-md p-2 text-slate-600 hover:bg-slate-200 hover:text-slate-900 transition-colors"
                        title="Download template"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <HoverBorderGradient
                    as="button"
                    containerClassName="w-full rounded-xl"
                    className={cn(
                      "w-full bg-slate-950 text-sm font-medium text-white",
                      isLoading && "opacity-70 cursor-not-allowed",
                    )}
                    onClick={handleCsvPredict}
                    aria-disabled={isLoading}
                  >
                    {csvPrediction.isPending
                      ? "Predicting..."
                      : "Predict from CSV"}
                  </HoverBorderGradient>
                </CardContent>
              </Card>
            </BackgroundGradient>
          </AnimatedContent>
        </section>

        {isLoading && (
          <FadeContent blur duration={550}>
            <Card className="border-cyan-300 bg-cyan-50 text-cyan-800">
              <CardContent className="space-y-4 py-6">
                <p className="text-sm font-medium">Running prediction...</p>
                <div className="space-y-3">
                  <div className="h-4 w-3/4 animate-pulse rounded bg-cyan-200" />
                  <div className="h-4 w-1/2 animate-pulse rounded bg-cyan-200" />
                  <div className="h-4 w-5/6 animate-pulse rounded bg-cyan-200" />
                </div>
              </CardContent>
            </Card>
          </FadeContent>
        )}

        {errorMessage && (
          <FadeContent blur duration={550}>
            <Card className="border-rose-300 bg-rose-50 text-rose-700 shadow-lg">
              <CardContent className="space-y-1 py-4 text-sm">
                <p className="inline-flex items-center gap-2 font-semibold">
                  <AlertTriangle className="h-4 w-4" />
                  Prediction failed
                </p>
                <p className="text-rose-600">{errorMessage}</p>
              </CardContent>
            </Card>
          </FadeContent>
        )}

        {result && (
          <AnimatedContent distance={44}>
            <section className="space-y-6" id="results">
              <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
                <Card className="border-slate-200 bg-white/95 shadow-xl shadow-slate-200/40">
                  <CardHeader>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <CardTitle className="text-slate-900">
                        Prediction Result
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={exportResultAsJSON}
                          className="rounded-md p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                          title="Export as JSON"
                        >
                          <FileJson className="h-4 w-4" />
                        </button>
                        {result.insight_source && (
                          <Badge className="border-slate-300 bg-slate-100 text-slate-700">
                            {result.insight_source === "GENAI_LLM" && (
                              <Sparkles className="mr-1 h-3 w-3" />
                            )}
                            {result.insight_source === "GENAI_LLM"
                              ? "GenAI Insight"
                              : "Rule Insight"}
                          </Badge>
                        )}
                        <Badge className={RISK_BADGE_STYLES[result.risk_level]} title={`Risk probability: ${probabilityLabel}`}>
                          {result.risk_level}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-start justify-between gap-2">
                      <CardDescription className="flex-1 text-slate-600">
                        {result.insight_summary ??
                          "Top-level summary from the prediction response."}
                      </CardDescription>
                      <button
                        onClick={handleCopySummary}
                        className="flex-shrink-0 rounded-md p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                        title="Copy summary"
                      >
                        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                      </button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-white shadow-sm">
                        <CardContent className="space-y-1 py-5">
                          <p className="text-xs uppercase tracking-wider text-slate-600">
                            Risk Probability
                          </p>
                          <p className="text-2xl font-semibold text-slate-900">
                            {probabilityLabel}
                          </p>
                        </CardContent>
                      </Card>
                      <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-white shadow-sm">
                        <CardContent className="space-y-1 py-5">
                          <p className="text-xs uppercase tracking-wider text-slate-600">
                            Confidence
                          </p>
                          <p className="text-2xl font-semibold text-slate-900">
                            {confidenceLabel}
                          </p>
                        </CardContent>
                      </Card>
                      <Card className="border-slate-200 bg-gradient-to-br from-slate-50 to-white shadow-sm">
                        <CardContent className="space-y-1 py-5">
                          <p className="inline-flex items-center gap-2 text-xs uppercase tracking-wider text-slate-600">
                            <Gauge className="h-3.5 w-3.5" />
                            Records Predicted
                          </p>
                          <p className="text-2xl font-semibold text-slate-900">
                            {result.total_records}
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    {result.data_warnings && result.data_warnings.length > 0 && (
                      <Card className="border-amber-300 bg-amber-50/70 shadow-md">
                        <CardContent className="space-y-2 py-4">
                          <p className="inline-flex items-center gap-2 text-sm font-semibold text-amber-900">
                            <AlertTriangle className="h-4 w-4" />
                            Data quality warnings
                          </p>
                          <ul className="space-y-1 text-sm text-amber-800">
                            {result.data_warnings.map((warning) => (
                              <li key={warning}>• {warning}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}

                    {batchRows.length > 1 && (
                      <Card className="border-slate-200 bg-slate-50">
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-base text-slate-900">
                              Batch Preview
                            </CardTitle>
                            <Badge className="border-slate-300 bg-slate-100 text-slate-700">
                              {batchRows.length} of {result.total_records}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow className="border-slate-200 hover:bg-transparent">
                                <TableHead className="text-slate-600">Row</TableHead>
                                <TableHead className="text-slate-600">Risk</TableHead>
                                <TableHead className="text-right text-slate-600">
                                  Probability
                                </TableHead>
                                <TableHead className="text-right text-slate-600">
                                  Confidence
                                </TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {batchRows.map((item, index) => (
                                <TableRow
                                  key={`${item.risk_level}-${index}`}
                                  className={cn(
                                    "border-slate-200 transition-colors hover:bg-slate-50",
                                    index % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                                  )}
                                >
                                  <TableCell className="text-slate-700">
                                    #{index + 1}
                                  </TableCell>
                                  <TableCell className="text-slate-900">
                                    {item.risk_level}
                                  </TableCell>
                                  <TableCell className="text-right text-slate-700">
                                    {(item.risk_probability * 100).toFixed(2)}%
                                  </TableCell>
                                  <TableCell className="text-right text-slate-700">
                                    {(item.confidence * 100).toFixed(2)}%
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>
                    )}
                  </CardContent>
                </Card>

              <Card className="border-slate-200 bg-white/95 shadow-xl shadow-slate-200/40">
                  <CardHeader>
                    <CardTitle className="text-slate-900">
                      Meaningful Insight
                    </CardTitle>
                    <CardDescription className="text-slate-600">
                    Row-specific drivers based on normalized inputs and
                    maintenance heuristics.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-200 hover:bg-transparent">
                          <TableHead className="text-slate-600">Driver</TableHead>
                          <TableHead className="text-slate-600">Observed</TableHead>
                          <TableHead className="text-right text-slate-600">
                            Impact
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {insightRows.length === 0 && (
                          <TableRow className="border-slate-200">
                            <TableCell className="text-slate-600">
                              No insight drivers returned.
                            </TableCell>
                            <TableCell />
                            <TableCell />
                          </TableRow>
                        )}
                        {insightRows.map((driver) => (
                          <TableRow
                            key={`${driver.factor}-${driver.observed_value}`}
                            className="border-slate-200 transition-colors hover:bg-slate-50"
                          >
                            <TableCell className="space-y-1 text-slate-900">
                              <p className="font-medium">{driver.factor}</p>
                              <p className="text-xs text-slate-600">
                                {driver.explanation}
                              </p>
                            </TableCell>
                            <TableCell className="text-slate-700">
                              {driver.observed_value}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="inline-flex items-center gap-2">
                                <Badge className={DRIVER_BADGE_STYLES[driver.direction]}>
                                  {driver.direction === "RISK_UP" && (
                                    <ArrowUpRight className="mr-1 h-3 w-3" />
                                  )}
                                  {driver.direction === "RISK_DOWN" && (
                                    <ArrowDownRight className="mr-1 h-3 w-3" />
                                  )}
                                  {driver.direction === "NEUTRAL" && (
                                    <Info className="mr-1 h-3 w-3" />
                                  )}
                                  {driver.direction.replace("_", " ")}
                                </Badge>
                                <span className="text-sm text-slate-700">
                                  {(driver.impact * 100).toFixed(0)}%
                                </span>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>

                    {recommendationRows.length > 0 && (
                      <Card className="border-slate-200 bg-slate-50">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-base text-slate-900">
                            Recommended Actions
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          {recommendationRows.map((recommendation, idx) => (
                            <div
                              key={recommendation.action}
                              className="rounded-lg border border-slate-200 bg-white p-3 transition-all hover:shadow-md"
                              style={{ animationDelay: `${idx * 50}ms` }}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <p className="text-sm font-medium text-slate-900">
                                  {recommendation.action}
                                </p>
                                <Badge
                                  className={
                                    PRIORITY_BADGE_STYLES[recommendation.priority]
                                  }
                                >
                                  {recommendation.priority}
                                </Badge>
                              </div>
                              <p className="mt-1 text-xs text-slate-600">
                                {recommendation.rationale}
                              </p>
                            </div>
                          ))}
                        </CardContent>
                      </Card>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card className="border-slate-200 bg-white/95 shadow-xl shadow-slate-200/40">
                <CardHeader>
                  <CardTitle className="text-slate-900">
                    Feature Importance (Global)
                  </CardTitle>
                  <CardDescription className="text-slate-600">
                    Model-level feature weights. These percentages are global
                    model influence, not this row specific local contribution.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-200 hover:bg-transparent">
                        <TableHead className="text-slate-600">Feature</TableHead>
                        <TableHead className="text-right text-slate-600">
                          Importance
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {featureRows.length === 0 && (
                        <TableRow className="border-slate-200">
                          <TableCell className="text-slate-600">
                            No feature importance returned.
                          </TableCell>
                          <TableCell />
                        </TableRow>
                      )}
                      {featureRows.map(({ feature, importance }) => (
                        <TableRow key={feature} className="border-slate-200 transition-colors hover:bg-slate-50">
                          <TableCell className="capitalize text-slate-900">
                            {feature.replace(/_/g, " ")}
                          </TableCell>
                          <TableCell className="text-right text-slate-700">
                            {(importance * 100).toFixed(2)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </section>
          </AnimatedContent>
        )}

        <AnimatedContent distance={34} delay={0.05}>
          <Card className="border-slate-200 bg-white/95 shadow-sm shadow-slate-200/60">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-slate-900">
                Input and Model Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="input-spec" className="border-slate-200">
                  <AccordionTrigger className="text-slate-900 hover:no-underline">
                    Minimum input schema
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600">
                    mileage, engine_hours, fault_codes, service_history, and
                    usage_patterns are required for manual and CSV workflows.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="latency" className="border-slate-200">
                  <AccordionTrigger className="text-slate-900 hover:no-underline">
                    Performance
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600">
                    The backend warms the model once at startup and keeps
                    per-request prediction latency low.
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="model-info" className="border-slate-200">
                  <AccordionTrigger className="text-slate-900 hover:no-underline">
                    Risk thresholds
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600">
                    LOW &lt; 0.30, MEDIUM 0.30-0.69, HIGH &gt;= 0.70. Risk
                    probability is the model output for HIGH risk. Confidence
                    is max(probability, 1 - probability).
                  </AccordionContent>
                </AccordionItem>
                <AccordionItem value="importance-info" className="border-slate-200">
                  <AccordionTrigger className="text-slate-900 hover:no-underline">
                    Why feature importance can look confusing
                  </AccordionTrigger>
                  <AccordionContent className="text-slate-600">
                    Feature importance values are global model weights, not
                    per-row explanations. Use the Meaningful Insight section
                    for row-specific operational interpretation.
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </AnimatedContent>
      </div>
    </main>
  );
}

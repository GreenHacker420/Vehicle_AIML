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
import { useMemo, useState, useEffect } from "react";

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
  RISK_UP: "border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-50 w-24 justify-center",
  RISK_DOWN: "border-emerald-300 bg-emerald-50 text-emerald-700 hover:bg-emerald-50 w-24 justify-center",
  NEUTRAL: "border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-100 w-24 justify-center",
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
  const [activeTab, setActiveTab] = useState<"manual" | "csv">("manual");

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
  useEffect(() => {
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
            <CardContent className="space-y-4 p-6 text-center md:p-8">
              <Badge className="mx-auto w-fit border-slate-300 bg-slate-100 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-700">
                Predict
              </Badge>
              <h1 className="mx-auto max-w-4xl text-center text-4xl font-extrabold leading-tight tracking-tight md:text-6xl bg-gradient-to-r from-slate-900 via-cyan-800 to-slate-900 bg-clip-text text-transparent pb-2 drop-shadow-sm hover:scale-[1.01] transition-transform duration-500">
                Maintenance Risk Intelligence
              </h1>
              <FadeContent blur duration={900} delay={240}>
                <p className="mx-auto max-w-3xl text-sm text-slate-700 md:text-lg">
                  Analyze maintenance risk from manual entries or bulk CSV data
                  using a single advanced prediction workspace.
                </p>
              </FadeContent>
            </CardContent>
          </Card>
        </AnimatedContent>

        <section className="mx-auto w-full max-w-5xl">
          <AnimatedContent distance={50} delay={0.05}>
            <BackgroundGradient className="rounded-3xl">
              <Card className="flex flex-col border-white/40 bg-white/60 backdrop-blur-lg shadow-2xl overflow-hidden rounded-3xl">
                <CardHeader className="border-b border-white/30 pb-4 bg-white/30">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <CardTitle className="text-slate-900 text-xl font-bold tracking-tight">Prediction Engine</CardTitle>
                      <CardDescription className="text-slate-700">
                        Select an input method to analyze fleet maintenance risk profiles.
                      </CardDescription>
                    </div>
                    <div className="flex bg-white/50 backdrop-blur-md p-1 rounded-xl w-fit shadow-inner border border-white/40">
                      <button
                        onClick={() => setActiveTab('manual')}
                        className={cn("px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm", activeTab === 'manual' ? "bg-white text-cyan-800" : "text-slate-600 hover:text-slate-900 transparent")}
                      >
                        Manual Entry
                      </button>
                      <button
                        onClick={() => setActiveTab('csv')}
                        className={cn("px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm", activeTab === 'csv' ? "bg-white text-orange-700" : "text-slate-600 hover:text-slate-900 transparent")}
                      >
                        CSV Batch
                      </button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-6">
                  {activeTab === 'manual' ? (
                    <div className="flex flex-col gap-4">
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                        <Input
                          type="number"
                          min={0}
                          placeholder="Mileage (e.g. 64000)"
                          value={manualForm.mileage}
                          onChange={(event) =>
                            handleInputChange("mileage", event.target.value)
                          }
                          className="focus:ring-2 focus:ring-cyan-500 bg-white/70"
                        />
                        <Input
                          type="number"
                          min={0}
                          placeholder="Engine Hours (e.g. 1200)"
                          value={manualForm.engine_hours}
                          onChange={(event) =>
                            handleInputChange("engine_hours", event.target.value)
                          }
                          className="focus:ring-2 focus:ring-cyan-500 bg-white/70"
                        />
                        <Input
                          placeholder="Service History (good, average, poor)"
                          value={manualForm.service_history}
                          onChange={(event) =>
                            handleInputChange("service_history", event.target.value)
                          }
                          className="focus:ring-2 focus:ring-cyan-500 bg-white/70"
                        />
                      </div>
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <Textarea
                          placeholder="Fault Codes (e.g. P0171, P0420)"
                          value={manualForm.fault_codes}
                          onChange={(event) =>
                            handleInputChange("fault_codes", event.target.value)
                          }
                          className="min-h-16 border-slate-200 bg-white/70 text-slate-900 focus:ring-2 focus:ring-cyan-500"
                        />
                        <Textarea
                          placeholder="Usage Patterns (mixed city driving, etc.)"
                          value={manualForm.usage_patterns}
                          onChange={(event) =>
                            handleInputChange("usage_patterns", event.target.value)
                          }
                          className="min-h-16 border-slate-200 bg-white/70 text-slate-900 focus:ring-2 focus:ring-cyan-500"
                        />
                      </div>
                      <div className="flex gap-4 pt-2">
                        <button
                          className={cn(
                            "flex-1 w-full rounded-xl bg-slate-900 hover:bg-slate-800 hover:shadow-lg hover:-translate-y-0.5 text-sm font-semibold text-white transition-all duration-300 active:scale-95 py-3",
                            isLoading && "opacity-70 cursor-not-allowed hover:-translate-y-0 hover:shadow-none active:scale-100",
                          )}
                          onClick={handleManualPredict}
                          disabled={isLoading}
                        >
                          {manualPrediction.isPending
                            ? "Predicting..."
                            : "Run Predict Engine (Ctrl+Enter)"}
                        </button>
                        <button
                          onClick={handleClearForm}
                          className="rounded-xl border border-slate-300 bg-white/50 px-6 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-white"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4">
                      <FileUpload onChange={handleCsvChange} />
                      <div className="flex w-full items-center justify-between rounded-xl border border-slate-200/50 bg-white/50 px-4 py-3 text-xs shadow-inner">
                        <div className="flex items-center gap-3">
                          <div className="rounded-full bg-orange-100 p-2 text-orange-600">
                            <UploadCloud className="h-4 w-4" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">Required CSV Schema</p>
                            <p className="text-slate-600 mt-0.5">mileage, engine_hours, fault_codes, service_history, usage_patterns</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="font-mono text-[10px] bg-slate-100 text-slate-500 px-2 py-1 rounded">
                            {csvFile?.name ? <span className="text-slate-800 font-medium">1 file attached</span> : "0 files selected"}
                          </span>
                          <button
                            onClick={downloadCSVTemplate}
                            className="flex-shrink-0 rounded-md bg-white p-2 text-slate-600 shadow-sm border border-slate-200 hover:bg-slate-50 hover:text-slate-900 transition-colors tooltip tooltip-left"
                            title="Download template"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                      <div className="pt-2">
                        <button
                          className={cn(
                            "w-full rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 hover:from-slate-800 hover:to-slate-700 hover:shadow-lg hover:-translate-y-0.5 text-sm font-semibold text-white transition-all duration-300 active:scale-95 py-3",
                            isLoading && "opacity-70 cursor-not-allowed hover:-translate-y-0 hover:shadow-none active:scale-100",
                          )}
                          onClick={handleCsvPredict}
                          disabled={isLoading}
                        >
                          {csvPrediction.isPending
                            ? "Analyzing batch..."
                            : "Predict from Dataset"}
                        </button>
                      </div>
                    </div>
                  )}
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
            <section className="mx-auto w-full max-w-5xl space-y-4" id="results">

              <div className="grid gap-4 md:grid-cols-12">
                {/* Result Summary Hero */}
                <Card className="flex flex-col justify-between border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl md:col-span-8 overflow-hidden">
                  <div className="p-6 md:p-8">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                      <h2 className="text-xl font-bold tracking-tight text-slate-900">
                        Prediction Result
                      </h2>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={exportResultAsJSON}
                          className="rounded-full bg-white/50 p-2 text-slate-600 shadow-sm border border-slate-200/50 hover:bg-white hover:text-slate-900 transition-colors"
                          title="Export as JSON"
                        >
                          <FileJson className="h-4 w-4" />
                        </button>
                        {result.insight_source && (
                          <Badge className="border border-white/40 bg-white/50 backdrop-blur-md text-slate-700 shadow-sm px-3 rounded-full">
                            {result.insight_source === "GENAI_LLM" && (
                              <Sparkles className="mr-1 h-3 w-3 text-indigo-500" />
                            )}
                            {result.insight_source === "GENAI_LLM"
                              ? "GenAI Insight"
                              : "Rule Insight"}
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col gap-6">
                      <div className="flex items-end gap-4">
                        <div className={cn("flex flex-col justify-center px-6 py-4 rounded-2xl border shadow-sm", RISK_BADGE_STYLES[result.risk_level])}>
                          <span className="text-xs uppercase tracking-wider font-bold opacity-80 mb-1">Risk Level</span>
                          <span className="text-3xl font-black">{result.risk_level}</span>
                        </div>
                        <div className="flex flex-col pb-1">
                          <span className="text-sm font-medium text-slate-500 uppercase tracking-widest">Probability</span>
                          <span className="text-4xl font-light tracking-tighter text-slate-900">{probabilityLabel}</span>
                        </div>
                      </div>

                      <div className="relative group rounded-2xl bg-white/40 p-4 border border-white/50 shadow-inner">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-slate-700 leading-relaxed font-medium">
                            {result.insight_summary ?? "Standard insight summary unavailable."}
                          </p>
                          <button
                            onClick={handleCopySummary}
                            className="flex-shrink-0 rounded-full bg-white p-2 text-slate-400 shadow-sm border border-slate-200 opacity-80 hover:opacity-100 hover:text-slate-800 transition-all"
                            title="Copy summary"
                          >
                            {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Micro Stats */}
                <div className="flex flex-col gap-4 md:col-span-4">
                  <div className="flex-1 flex flex-col justify-center p-6 border border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Model Confidence</p>
                    <p className="text-4xl font-light tracking-tight text-slate-900">{confidenceLabel}</p>
                    <div className="mt-4 h-1.5 w-full rounded-full bg-slate-200/50 overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${result.confidence * 100}%` }} />
                    </div>
                  </div>
                  <div className="flex-1 flex flex-col justify-center p-6 border border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl">
                    <div className="flex items-center gap-2 mb-2">
                      <Gauge className="h-4 w-4 text-slate-400" />
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Records Scored</p>
                    </div>
                    <p className="text-4xl font-light tracking-tight text-slate-900">{result.total_records.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {result.data_warnings && result.data_warnings.length > 0 && (
                <div className="rounded-2xl border border-amber-300/50 bg-amber-50/80 backdrop-blur-lg px-6 py-4 shadow-sm">
                  <p className="inline-flex items-center gap-2 text-sm font-semibold text-amber-900 mb-2">
                    <AlertTriangle className="h-4 w-4" />
                    Data Quality Warnings
                  </p>
                  <ul className="space-y-1 text-sm text-amber-800">
                    {result.data_warnings.map((warning, i) => (
                      <li key={i}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid gap-4 lg:grid-cols-12">
                {/* Insights and Actions Col */}
                <div className="flex flex-col gap-4 lg:col-span-7">
                  <Card className="flex flex-col border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl overflow-hidden">
                    <CardHeader className="bg-white/30 border-b border-white/20 pb-4">
                      <CardTitle className="text-lg text-slate-900">Meaningful Insight Drivers</CardTitle>
                      <CardDescription className="text-slate-600 text-xs">
                        Local heuristic reasoning normalized.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <Table>
                        <TableHeader className="bg-slate-50/50">
                          <TableRow className="border-b border-white/20 hover:bg-transparent">
                            <TableHead className="text-slate-500 font-semibold px-6 text-xs h-10">Driver</TableHead>
                            <TableHead className="text-slate-500 font-semibold text-xs h-10">Observed</TableHead>
                            <TableHead className="text-right text-slate-500 font-semibold px-6 text-xs h-10">Impact</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {insightRows.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={3} className="text-center text-slate-500 py-8">No insight drivers returned.</TableCell>
                            </TableRow>
                          )}
                          {insightRows.map((driver) => (
                            <TableRow key={`${driver.factor}-${driver.observed_value}`} className="border-b border-white/20 transition-all duration-200 hover:bg-cyan-50/40">
                              <TableCell className="px-6 py-3 min-w-[240px]">
                                <p className="font-semibold text-slate-900 text-sm whitespace-nowrap overflow-hidden text-ellipsis w-48">{driver.factor}</p>
                                <p className="text-[11px] text-slate-500 mt-0.5 max-w-[280px] line-clamp-2">{driver.explanation}</p>
                              </TableCell>
                              <TableCell className="text-sm font-mono text-slate-700 py-3">{driver.observed_value}</TableCell>
                              <TableCell className="text-right px-6 py-3">
                                <div className="inline-flex items-center gap-2">
                                  <Badge className={cn("px-2 py-0.5 rounded text-[10px] shadow-sm", DRIVER_BADGE_STYLES[driver.direction])}>
                                    {driver.direction === "RISK_UP" && <ArrowUpRight className="mr-1 h-3 w-3" />}
                                    {driver.direction === "RISK_DOWN" && <ArrowDownRight className="mr-1 h-3 w-3" />}
                                    {driver.direction === "NEUTRAL" && <Info className="mr-1 h-3 w-3" />}
                                    {driver.direction.replace("_", " ")}
                                  </Badge>
                                  <span className="text-xs font-bold text-slate-700 w-8 text-right">
                                    {(driver.impact * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  {recommendationRows.length > 0 && (
                    <Card className="flex flex-col border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl overflow-hidden">
                      <CardHeader className="bg-white/30 border-b border-white/20 pb-4">
                        <CardTitle className="text-lg text-slate-900">Recommended Actions</CardTitle>
                      </CardHeader>
                      <CardContent className="p-4 space-y-3">
                        {recommendationRows.map((recommendation, idx) => (
                          <div
                            key={recommendation.action}
                            className="rounded-2xl border border-white/50 bg-white/70 p-4 shadow-sm hover:shadow-md transition-all"
                            style={{ animationDelay: `${idx * 50}ms` }}
                          >
                            <div className="flex items-start justify-between gap-4 mb-1">
                              <p className="text-sm font-bold text-slate-900 leading-tight">
                                {recommendation.action}
                              </p>
                              <Badge className={cn("shadow-sm rounded capitalize text-[10px] px-2 py-0.5", PRIORITY_BADGE_STYLES[recommendation.priority])}>
                                {recommendation.priority}
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-600">
                              {recommendation.rationale}
                            </p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Stats & Batch Col */}
                <div className="flex flex-col gap-4 lg:col-span-5">
                  <Card className="flex flex-col border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl overflow-hidden">
                    <CardHeader className="bg-white/30 border-b border-white/20 pb-4">
                      <div className="flex items-center gap-2">
                        <Gauge className="h-4 w-4 text-cyan-600" />
                        <CardTitle className="text-lg text-slate-900">Feature Importance</CardTitle>
                      </div>
                      <CardDescription className="text-slate-600 text-xs">
                        Global model weights impact.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <Table>
                        <TableBody>
                          {featureRows.length === 0 && (
                            <TableRow>
                              <TableCell className="text-center text-slate-500 py-6">No features returned.</TableCell>
                            </TableRow>
                          )}
                          {featureRows.map(({ feature, importance }) => (
                            <TableRow key={feature} className="border-b border-white/20 hover:bg-white/40">
                              <TableCell className="capitalize text-sm font-medium text-slate-800 px-6 py-3">
                                {feature.replace(/_/g, " ")}
                              </TableCell>
                              <TableCell className="text-right px-6 py-3">
                                <div className="flex items-center justify-end gap-3">
                                  <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200/50 shadow-inner">
                                    <div
                                      className="h-full bg-cyan-500 rounded-full"
                                      style={{ width: `${importance * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-mono font-medium text-slate-700 w-10 text-right">
                                    {(importance * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  {batchRows.length > 1 && (
                    <Card className="flex flex-col border-white/40 bg-white/60 backdrop-blur-lg shadow-xl rounded-3xl overflow-hidden">
                      <CardHeader className="bg-white/30 border-b border-white/20 pb-4 flex flex-row items-center justify-between">
                        <CardTitle className="text-lg text-slate-900">Batch Preview</CardTitle>
                        <Badge className="bg-slate-800 text-white rounded-full px-3">{batchRows.length} shown</Badge>
                      </CardHeader>
                      <CardContent className="p-0">
                        <Table>
                          <TableHeader className="bg-slate-50/50">
                            <TableRow className="border-b border-white/20 hover:bg-transparent">
                              <TableHead className="text-slate-500 font-semibold text-xs px-6 h-9">Row</TableHead>
                              <TableHead className="text-slate-500 font-semibold text-xs h-9">Level</TableHead>
                              <TableHead className="text-right text-slate-500 font-semibold text-xs px-6 h-9">Prob.</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {batchRows.map((item, index) => (
                              <TableRow key={`${item.risk_level}-${index}`} className="border-b border-white/20 hover:bg-white/40">
                                <TableCell className="text-xs font-mono px-6 py-2 text-slate-500">#{index + 1}</TableCell>
                                <TableCell className="py-2">
                                  <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded shadow-sm", RISK_BADGE_STYLES[item.risk_level])}>
                                    {item.risk_level}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right text-xs font-mono text-slate-700 px-6 py-2">
                                  {(item.risk_probability * 100).toFixed(1)}%
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </section>
          </AnimatedContent>
        )}

        <AnimatedContent distance={34} delay={0.05}>
          <section className="mx-auto w-full max-w-5xl">
            <Card className="border-white/40 bg-white/40 backdrop-blur-xl shadow-lg rounded-3xl overflow-hidden">
              <CardHeader className="pb-2 bg-white/20">
                <CardTitle className="text-sm font-semibold text-slate-900 uppercase tracking-widest px-2">
                  Reference Notes
                </CardTitle>
              </CardHeader>
              <CardContent className="px-6 py-2">
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="input-spec" className="border-white/20">
                    <AccordionTrigger className="text-sm font-medium text-slate-800 hover:text-cyan-700 hover:no-underline transition-colors py-3">
                      Minimum input schema
                    </AccordionTrigger>
                    <AccordionContent className="text-slate-600 text-sm leading-relaxed pb-4">
                      <code className="bg-white/60 px-1 py-0.5 rounded text-slate-800">mileage</code>, <code className="bg-white/60 px-1 py-0.5 rounded text-slate-800">engine_hours</code>, <code className="bg-white/60 px-1 py-0.5 rounded text-slate-800">fault_codes</code>, <code className="bg-white/60 px-1 py-0.5 rounded text-slate-800">service_history</code>, and <code className="bg-white/60 px-1 py-0.5 rounded text-slate-800">usage_patterns</code> are required for manual and CSV workflows.
                    </AccordionContent>
                  </AccordionItem>
                  <AccordionItem value="latency" className="border-white/20">
                    <AccordionTrigger className="text-sm font-medium text-slate-800 hover:text-cyan-700 hover:no-underline transition-colors py-3">
                      Performance Architecture
                    </AccordionTrigger>
                    <AccordionContent className="text-slate-600 text-sm leading-relaxed pb-4">
                      The backend warms the model once at startup and keeps per-request prediction latency low using persistent inference sessions.
                    </AccordionContent>
                  </AccordionItem>
                  <AccordionItem value="model-info" className="border-transparent">
                    <AccordionTrigger className="text-sm font-medium text-slate-800 hover:text-cyan-700 hover:no-underline transition-colors py-3">
                      Risk thresholds
                    </AccordionTrigger>
                    <AccordionContent className="text-slate-600 text-sm leading-relaxed pb-4">
                      LOW &lt; 0.30, MEDIUM 0.30-0.69, HIGH &gt;= 0.70. Risk calculations incorporate temporal decay and heuristics normalization.
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </CardContent>
            </Card>
          </section>
        </AnimatedContent>
      </div>
    </main>
  );
}

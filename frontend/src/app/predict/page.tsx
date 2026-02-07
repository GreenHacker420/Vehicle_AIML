"use client";

import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, Gauge, Upload } from "lucide-react";
import { ChangeEvent, FormEvent, useMemo, useState } from "react";

import { BackgroundGradient } from "@/components/aceternity/background-gradient";
import {
  AceternityInput,
  AceternityTextArea,
} from "@/components/aceternity/input";
import { HoverBorderButton } from "@/components/aceternity/hover-border-button";
import { AceternityFeatureTable } from "@/components/aceternity/table";
import {
  ManualPredictionInput,
  PredictionResponse,
  predictFromCsvFile,
  predictFromManualInput,
} from "@/services/predictionService";

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

const RISK_STYLES: Record<"LOW" | "MEDIUM" | "HIGH", string> = {
  LOW: "border-emerald-300/40 bg-emerald-400/15 text-emerald-200",
  MEDIUM: "border-amber-300/40 bg-amber-400/15 text-amber-200",
  HIGH: "border-rose-300/40 bg-rose-400/15 text-rose-200",
};

export default function PredictPage() {
  const [manualForm, setManualForm] = useState<ManualFormState>(INITIAL_FORM);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const manualPrediction = useMutation({
    mutationFn: (payload: ManualPredictionInput) => predictFromManualInput(payload),
    onSuccess: (response) => {
      setResult(response);
      setErrorMessage(null);
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
    return Object.entries(result.feature_importance).map(([feature, importance]) => ({
      feature,
      importance,
    }));
  }, [result]);

  const confidenceLabel = result
    ? `${(result.confidence * 100).toFixed(2)}%`
    : "--";

  const handleInputChange = (
    key: keyof ManualFormState,
    value: string,
  ): void => {
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

  const handleManualSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
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
      setErrorMessage("Please complete all manual input fields before predicting.");
      return;
    }

    manualPrediction.mutate(payload);
  };

  const handleCsvSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetError();

    if (!csvFile) {
      setErrorMessage("Select a CSV file before running prediction.");
      return;
    }

    csvPrediction.mutate(csvFile);
  };

  const handleCsvSelect = (event: ChangeEvent<HTMLInputElement>) => {
    setCsvFile(event.target.files?.[0] ?? null);
    resetError();
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-4 pb-12 pt-10 md:px-8">
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="space-y-3"
      >
        <p className="inline-flex rounded-full border border-cyan-200/30 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-200">
          FleetAI Milestone-1
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100 md:text-5xl">
          Vehicle Maintenance Prediction
        </h1>
        <p className="max-w-3xl text-sm text-slate-300 md:text-base">
          Enter vehicle data manually or upload a CSV to predict maintenance
          risk level, confidence score, and feature importance.
        </p>
      </motion.section>

      <section className="grid gap-5 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.05 }}
        >
          <BackgroundGradient className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Manual Input</h2>
              <p className="text-sm text-slate-300">
                Required fields: mileage, engine hours, fault codes, service
                history, and usage patterns.
              </p>
            </div>

            <form className="space-y-3" onSubmit={handleManualSubmit}>
              <AceternityInput
                type="number"
                min={0}
                placeholder="Mileage (e.g. 64000)"
                value={manualForm.mileage}
                onChange={(event) =>
                  handleInputChange("mileage", event.target.value)
                }
                required
              />
              <AceternityInput
                type="number"
                min={0}
                placeholder="Engine Hours (e.g. 1200)"
                value={manualForm.engine_hours}
                onChange={(event) =>
                  handleInputChange("engine_hours", event.target.value)
                }
                required
              />
              <AceternityTextArea
                placeholder="Fault Codes (comma-separated, e.g. P0171, P0420)"
                value={manualForm.fault_codes}
                onChange={(event) =>
                  handleInputChange("fault_codes", event.target.value)
                }
                required
              />
              <AceternityInput
                placeholder="Service History (e.g. good / average / poor)"
                value={manualForm.service_history}
                onChange={(event) =>
                  handleInputChange("service_history", event.target.value)
                }
                required
              />
              <AceternityTextArea
                placeholder="Usage Patterns (e.g. mixed city driving)"
                value={manualForm.usage_patterns}
                onChange={(event) =>
                  handleInputChange("usage_patterns", event.target.value)
                }
                required
              />
              <HoverBorderButton type="submit" isLoading={manualPrediction.isPending}>
                Predict from Manual Data
              </HoverBorderButton>
            </form>
          </BackgroundGradient>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.12 }}
        >
          <BackgroundGradient className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">CSV Upload</h2>
              <p className="text-sm text-slate-300">
                Upload a CSV with manual fields or model-compatible columns.
              </p>
            </div>

            <form className="space-y-3" onSubmit={handleCsvSubmit}>
              <label className="relative block w-full cursor-pointer rounded-2xl border border-dashed border-cyan-200/40 bg-slate-900/50 p-4 text-sm text-slate-200 transition hover:border-cyan-200/70">
                <span className="mb-2 inline-flex items-center gap-2 text-cyan-200">
                  <Upload className="h-4 w-4" />
                  Select CSV File
                </span>
                <input
                  className="absolute inset-0 cursor-pointer opacity-0"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleCsvSelect}
                />
                <p className="truncate text-slate-300">
                  {csvFile ? csvFile.name : "No file selected"}
                </p>
              </label>

              <HoverBorderButton type="submit" isLoading={csvPrediction.isPending}>
                Predict from CSV
              </HoverBorderButton>
            </form>

            <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-3 text-xs text-slate-300">
              CSV expected columns include:
              <span className="mt-1 block text-slate-100">
                mileage, engine_hours, fault_codes, service_history,
                usage_patterns
              </span>
            </div>
          </BackgroundGradient>
        </motion.div>
      </section>

      {isLoading && (
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-2xl border border-cyan-200/30 bg-cyan-400/10 px-4 py-3 text-sm text-cyan-100"
        >
          Running prediction...
        </motion.section>
      )}

      {errorMessage && (
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-rose-300/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
        >
          <p className="inline-flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" />
            Prediction failed
          </p>
          <p className="mt-1">{errorMessage}</p>
        </motion.section>
      )}

      {result && (
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-5 lg:grid-cols-[1.2fr_1fr]"
        >
          <BackgroundGradient className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1">
                <h2 className="text-lg font-semibold text-white">
                  Prediction Result
                </h2>
                <p className="text-sm text-slate-300">
                  Showing top-level risk summary.
                </p>
              </div>
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold tracking-wide ${RISK_STYLES[result.risk_level]}`}
              >
                {result.risk_level}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Confidence
                </p>
                <p className="mt-1 text-2xl font-semibold text-slate-100">
                  {confidenceLabel}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
                <p className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
                  <Gauge className="h-3.5 w-3.5" />
                  Records Predicted
                </p>
                <p className="mt-1 text-2xl font-semibold text-slate-100">
                  {result.total_records}
                </p>
              </div>
            </div>

            {result.predictions && result.predictions.length > 1 && (
              <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
                <p className="mb-2 text-xs uppercase tracking-wide text-slate-400">
                  Batch Preview
                </p>
                <div className="overflow-hidden rounded-xl border border-white/10">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400">
                      <tr>
                        <th className="px-3 py-2">Row</th>
                        <th className="px-3 py-2">Risk</th>
                        <th className="px-3 py-2 text-right">Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.predictions.slice(0, 5).map((item, index) => (
                        <tr
                          key={`${item.risk_level}-${index}`}
                          className="border-t border-white/10"
                        >
                          <td className="px-3 py-2 text-slate-300">
                            #{index + 1}
                          </td>
                          <td className="px-3 py-2 text-slate-100">
                            {item.risk_level}
                          </td>
                          <td className="px-3 py-2 text-right text-slate-200">
                            {(item.confidence * 100).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </BackgroundGradient>

          <BackgroundGradient className="space-y-3">
            <h3 className="text-lg font-semibold text-white">
              Feature Importance
            </h3>
            <p className="text-sm text-slate-300">
              Top contributing features returned by the backend model.
            </p>
            <AceternityFeatureTable rows={featureRows} />
          </BackgroundGradient>
        </motion.section>
      )}
    </main>
  );
}


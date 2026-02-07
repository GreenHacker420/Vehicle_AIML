import { cva } from "class-variance-authority";
import {
  forwardRef,
  InputHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

const inputBase = cva(
  "w-full rounded-2xl border border-white/15 bg-slate-900/70 px-4 py-3 text-sm text-slate-100 shadow-sm outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-400/30",
);

type InputProps = InputHTMLAttributes<HTMLInputElement>;
type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export const AceternityInput = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return <input ref={ref} className={cn(inputBase(), className)} {...props} />;
  },
);

AceternityInput.displayName = "AceternityInput";

export const AceternityTextArea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          inputBase(),
          "min-h-24 resize-y leading-relaxed",
          className,
        )}
        {...props}
      />
    );
  },
);

AceternityTextArea.displayName = "AceternityTextArea";

import * as React from "react";
import { cn } from "@/lib/format";

export function Card({
  className,
  hover,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { hover?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-card)] border border-line bg-surface",
        hover &&
          "transition-[border-color,background-color,transform] duration-200 hover:-translate-y-px hover:border-line-strong hover:bg-surface-2",
        className,
      )}
      {...props}
    />
  );
}

export function Badge({
  className,
  tone = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: "neutral" | "brand" | "outline" }) {
  const tones = {
    neutral: "bg-surface-2 text-ink-secondary border-transparent",
    brand: "bg-brand-soft text-[#c3b5ff] border-brand-line",
    outline: "bg-transparent text-ink-muted border-line",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-medium leading-4",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}

export function SectionLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted",
        className,
      )}
      {...props}
    />
  );
}

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

export function Button({
  className,
  variant = "secondary",
  size = "md",
  ...props
}: ButtonProps) {
  const variants = {
    primary:
      "bg-brand text-white hover:bg-[#8f74ff] disabled:bg-[#3a3160] disabled:text-ink-faint shadow-[0_1px_0_0_#ffffff1f_inset]",
    secondary:
      "bg-surface-2 text-ink border border-line hover:border-line-strong hover:bg-surface-3 disabled:text-ink-faint",
    ghost: "bg-transparent text-ink-secondary hover:bg-surface-2 hover:text-ink",
    danger: "bg-transparent text-[#e07070] border border-[#d03b3b40] hover:bg-[#d03b3b1a]",
  };
  const sizes = {
    sm: "h-7 px-2.5 text-[12px] rounded-md gap-1.5",
    md: "h-9 px-3.5 text-[13px] rounded-lg gap-2",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-colors disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  );
}

/** Stat with an optional secondary line. Used across cards and detail headers. */
export function Stat({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0", className)}>
      <div className="truncate text-[11px] uppercase tracking-[0.08em] text-ink-muted">{label}</div>
      <div className="tabular mt-1 truncate text-[15px] font-semibold text-ink">{value}</div>
      {sub ? <div className="mt-0.5 truncate text-[11px] text-ink-faint">{sub}</div> : null}
    </div>
  );
}

export function Divider({ className }: { className?: string }) {
  return <div className={cn("h-px w-full bg-line", className)} />;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[var(--radius-card)] border border-dashed border-line-strong px-6 py-14 text-center">
      <span className="grid size-10 place-items-center rounded-xl bg-surface-2 text-ink-muted">
        <Icon className="size-5" />
      </span>
      <div className="mt-3 text-[14px] font-semibold text-ink">{title}</div>
      <p className="mt-1 max-w-md text-[13px] leading-relaxed text-ink-muted">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

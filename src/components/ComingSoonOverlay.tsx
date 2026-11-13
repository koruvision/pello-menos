import { BODY_SPLASH_LAUNCH_LABEL } from "@/lib/data";

type Props = {
  /** Tamanho do spinner e do texto. */
  size?: "sm" | "lg";
};

/**
 * Véu acinzentado com spinner para produto "em produção" (Body Splash até o
 * lançamento). Vai por cima da foto do card ou da ficha.
 */
export function ComingSoonOverlay({ size = "sm" }: Props) {
  const large = size === "lg";
  return (
    <div
      data-pm-coming-soon
      aria-label={`Em produção · lançamento ${BODY_SPLASH_LAUNCH_LABEL}`}
      className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-surface-container-high/80 text-center backdrop-grayscale"
    >
      <span
        aria-hidden
        className={`block rounded-full border-[3px] border-primary/20 border-t-primary ${
          large ? "h-14 w-14" : "h-9 w-9"
        }`}
        style={{ animation: "pm-coming-spin 0.9s linear infinite" }}
      />
      <span
        className={`rounded-full bg-primary px-3 py-1 font-semibold tracking-wide text-on-primary uppercase ${
          large ? "text-xs" : "text-[10px]"
        }`}
      >
        Em produção
      </span>
      <span className={`px-4 text-on-surface-variant ${large ? "text-sm" : "text-[11px]"}`}>
        Lançamento {BODY_SPLASH_LAUNCH_LABEL}
      </span>
      <style>{`@keyframes pm-coming-spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}

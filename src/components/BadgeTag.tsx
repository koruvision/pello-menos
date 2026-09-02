import { Icon, type IconName } from "@/components/Icon";

function iconForBadge(label: string): IconName {
  const key = label
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  if (key.includes("oferta")) return "badgePercent";
  if (key.includes("vendido")) return "star";
  if (key.includes("verao")) return "sun";
  if (key.includes("cera")) return "sparkle";
  if (key.includes("novo") || key.includes("novidade") || key.includes("lancamento")) {
    return "sparkles";
  }
  if (key.includes("corpo")) return "personStanding";
  if (key.includes("combo") || key.includes("pacote")) return "layoutGrid";
  if (key.includes("olhar")) return "scanFace";
  if (key.includes("tecnologia")) return "sparkle";
  return "tag";
}

type Props = {
  label: string;
  className?: string;
  size?: "sm" | "md";
};

export function BadgeTag({ label, className = "", size = "sm" }: Props) {
  const compact = size === "sm";

  return (
    <span
      className={`inline-flex w-fit items-center rounded-full border-2 border-primary bg-secondary-container font-bold tracking-wide text-on-secondary-container uppercase ${
        compact
          ? "gap-1.5 px-2 py-0.5 text-[10px]"
          : "gap-2 px-3 py-1 font-label-md text-label-md"
      } ${className}`}
    >
      <span
        className={`flex shrink-0 items-center justify-center rounded-full bg-primary ${
          compact ? "h-4 w-4" : "h-5 w-5"
        }`}
      >
        <Icon
          name={iconForBadge(label)}
          size={compact ? 10 : 12}
          className="text-secondary-container"
        />
      </span>
      {label}
    </span>
  );
}

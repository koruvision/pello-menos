"use client";

import { Icon } from "@/components/Icon";

const btnClass =
  "btn-lux btn-lux-ghost pointer-events-auto flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-white text-primary shadow-[0_10px_24px_rgba(112,0,83,0.22)] sm:h-11 sm:w-11 md:h-12 md:w-12";

type Props = {
  prevLabel: string;
  nextLabel: string;
  onPrev: () => void;
  onNext: () => void;
};

export function CarouselArrows({
  prevLabel,
  nextLabel,
  onPrev,
  onNext,
}: Props) {
  return (
    <div className="pointer-events-none absolute inset-0 z-30 flex items-center justify-between px-1 sm:px-2 md:px-3">
      <button
        type="button"
        aria-label={prevLabel}
        onClick={onPrev}
        className={btnClass}
      >
        <Icon name="chevronLeft" size={22} />
      </button>
      <button
        type="button"
        aria-label={nextLabel}
        onClick={onNext}
        className={btnClass}
      >
        <Icon name="chevronRight" size={22} />
      </button>
    </div>
  );
}

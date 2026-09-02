"use client";

import { useCallback, useEffect, useRef } from "react";

function paddingLeft(node: HTMLElement) {
  return parseFloat(getComputedStyle(node).paddingLeft) || 0;
}

function nearestIndex(node: HTMLElement, selector: string) {
  const cards = Array.from(node.querySelectorAll<HTMLElement>(selector));
  if (!cards.length) return 0;
  const origin = node.scrollLeft + paddingLeft(node);
  let best = 0;
  let dist = Infinity;
  cards.forEach((card, index) => {
    const delta = Math.abs(card.offsetLeft - origin);
    if (delta < dist) {
      dist = delta;
      best = index;
    }
  });
  return best;
}

export function useCardCarousel(selector = "[data-carousel-card]") {
  const scroller = useRef<HTMLDivElement>(null);
  const indexRef = useRef(0);
  const animatingRef = useRef(false);
  const moveRef = useRef(0);

  const goTo = useCallback(
    (index: number) => {
      const node = scroller.current;
      if (!node) return;
      const cards = Array.from(node.querySelectorAll<HTMLElement>(selector));
      if (!cards.length) return;
      const next = Math.max(0, Math.min(cards.length - 1, index));
      indexRef.current = next;
      animatingRef.current = true;
      const token = ++moveRef.current;
      node.style.scrollSnapType = "none";
      node.scrollTo({
        left: cards[next]!.offsetLeft - paddingLeft(node),
        behavior: "smooth",
      });
      const finish = () => {
        if (token !== moveRef.current) return;
        node.style.scrollSnapType = "";
        animatingRef.current = false;
      };
      node.addEventListener("scrollend", finish, { once: true });
      window.setTimeout(finish, 520);
    },
    [selector],
  );

  const scrollByCard = useCallback(
    (direction: number) => {
      const node = scroller.current;
      if (!node) return;
      if (!animatingRef.current) {
        indexRef.current = nearestIndex(node, selector);
      }
      goTo(indexRef.current + direction);
    },
    [goTo, selector],
  );

  useEffect(() => {
    const node = scroller.current;
    if (!node) return;

    let timer = 0;
    const sync = () => {
      if (animatingRef.current) return;
      indexRef.current = nearestIndex(node, selector);
    };
    const onScroll = () => {
      if (animatingRef.current) return;
      window.clearTimeout(timer);
      timer = window.setTimeout(sync, 120);
    };

    node.addEventListener("scrollend", sync);
    node.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.clearTimeout(timer);
      node.removeEventListener("scrollend", sync);
      node.removeEventListener("scroll", onScroll);
    };
  }, [selector]);

  return { scroller, scrollByCard };
}

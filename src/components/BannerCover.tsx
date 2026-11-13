import { getImageProps } from "next/image";

type Props = {
  src: string;
  srcMobile?: string;
  srcTablet?: string;
  alt: string;
  position?: string;
  positionMobile?: string;
  priority?: boolean;
  className?: string;
  sizes?: string;
  /** Arte com texto queimado — não cortar badge/preço. */
  contain?: boolean;
  /** object-contain só abaixo de md (ex.: texto queimado no mobile). */
  containMobile?: boolean;
};

export function BannerCover({
  src,
  srcMobile,
  srcTablet,
  alt,
  position = "50% 40%",
  positionMobile,
  priority = false,
  className = "",
  sizes = "100vw",
  contain = false,
  containMobile = false,
}: Props) {
  const mobilePos = positionMobile ?? position;
  const mobileSrc = srcMobile ?? src;
  const tabletSrc = srcTablet ?? src;
  const fitAll = contain;
  const fitMobileOnly = !contain && containMobile;

  const {
    props: { srcSet: desktopSrcSet },
  } = getImageProps({
    alt,
    src,
    fill: true,
    sizes,
    priority,
  });
  const {
    props: { srcSet: tabletSrcSet },
  } = getImageProps({
    alt,
    src: tabletSrc,
    fill: true,
    sizes,
    priority,
  });
  const {
    props: { srcSet: mobileSrcSet, ...mobileImg },
  } = getImageProps({
    alt,
    src: mobileSrc,
    fill: true,
    sizes: "100vw",
    priority,
  });

  const fitClass = fitAll
    ? "object-contain"
    : fitMobileOnly
      ? "object-contain md:object-cover"
      : "object-cover";

  const hasResponsive = Boolean(srcMobile || srcTablet);

  return (
    <div className={`absolute inset-0 overflow-hidden ${className}`}>
      <picture className="absolute inset-0 block">
        {hasResponsive ? (
          <source media="(min-width: 1024px)" srcSet={desktopSrcSet || src} />
        ) : null}
        {srcTablet || srcMobile ? (
          <source
            media="(min-width: 768px)"
            srcSet={tabletSrcSet || desktopSrcSet || src}
          />
        ) : null}
        <img
          {...mobileImg}
          alt={alt}
          srcSet={srcMobile ? mobileSrcSet : desktopSrcSet}
          className={`absolute inset-0 h-full w-full [object-position:var(--banner-pos-m)] md:[object-position:var(--banner-pos-d)] ${fitClass}${fitMobileOnly ? " js-hero-baked-m" : ""}`}
          style={{
            ...mobileImg.style,
            width: "100%",
            height: "100%",
            position: "absolute",
            inset: 0,
            objectFit: fitAll || fitMobileOnly ? "contain" : "cover",
            ["--banner-pos-m" as string]: mobilePos,
            ["--banner-pos-d" as string]: position,
          }}
        />
      </picture>
    </div>
  );
}

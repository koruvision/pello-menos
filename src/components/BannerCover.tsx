import { getImageProps } from "next/image";

type Props = {
  src: string;
  srcMobile?: string;
  alt: string;
  position?: string;
  positionMobile?: string;
  priority?: boolean;
  className?: string;
  sizes?: string;
};

export function BannerCover({
  src,
  srcMobile,
  alt,
  position = "50% 40%",
  positionMobile,
  priority = false,
  className = "",
  sizes = "100vw",
}: Props) {
  const mobilePos = positionMobile ?? position;
  const mobileSrc = srcMobile ?? src;
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
    props: { srcSet: mobileSrcSet, ...mobileImg },
  } = getImageProps({
    alt,
    src: mobileSrc,
    fill: true,
    sizes: "100vw",
    priority,
  });

  return (
    <picture className="absolute inset-0 block">
      {srcMobile ? (
        <source media="(min-width: 768px)" srcSet={desktopSrcSet} />
      ) : null}
      <img
        {...mobileImg}
        alt={alt}
        srcSet={srcMobile ? mobileSrcSet : desktopSrcSet}
        className={`absolute inset-0 h-full w-full object-cover [object-position:var(--banner-pos-m)] md:[object-position:var(--banner-pos-d)] ${className}`}
        style={{
          ...mobileImg.style,
          width: "100%",
          height: "100%",
          position: "absolute",
          inset: 0,
          ["--banner-pos-m" as string]: mobilePos,
          ["--banner-pos-d" as string]: position,
          transformOrigin: position,
        }}
      />
    </picture>
  );
}

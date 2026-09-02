import {
  ArrowRight,
  BadgePercent,
  ChevronLeft,
  ChevronRight,
  Check,
  Clock,
  CreditCard,
  Heart,
  House,
  LayoutGrid,
  Mail,
  MapPin,
  Minus,
  PersonStanding,
  Phone,
  Plus,
  QrCode,
  ScanFace,
  Search,
  ShieldCheck,
  ShoppingBag,
  ShoppingCart,
  Sparkle,
  Sparkles,
  Star,
  Sun,
  Tag,
  Trash2,
  Truck,
  User,
  X,
  type LucideProps,
} from "lucide-react";

const icons = {
  sparkles: Sparkles,
  star: Star,
  sun: Sun,
  tag: Tag,
  shoppingBag: ShoppingBag,
  shoppingCart: ShoppingCart,
  search: Search,
  user: User,
  close: X,
  house: House,
  creditCard: CreditCard,
  clock: Clock,
  arrowRight: ArrowRight,
  chevronLeft: ChevronLeft,
  chevronRight: ChevronRight,
  check: Check,
  minus: Minus,
  plus: Plus,
  trash: Trash2,
  sparkle: Sparkle,
  heart: Heart,
  personStanding: PersonStanding,
  scanFace: ScanFace,
  layoutGrid: LayoutGrid,
  truck: Truck,
  shieldCheck: ShieldCheck,
  badgePercent: BadgePercent,
  qrCode: QrCode,
  mail: Mail,
  mapPin: MapPin,
  phone: Phone,
} as const;

export type IconName = keyof typeof icons;

type IconProps = {
  name: IconName;
  className?: string;
  size?: number;
  filled?: boolean;
};

export function Icon({
  name,
  className,
  size = 20,
  filled = false,
}: IconProps) {
  const Cmp = icons[name];
  const props: LucideProps = {
    "aria-hidden": true,
    className,
    size,
    strokeWidth: filled ? 2 : 1.5,
  };

  if (filled) {
    props.fill = "currentColor";
  }

  return <Cmp {...props} />;
}

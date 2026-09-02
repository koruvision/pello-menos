import { Icon, type IconName } from "@/components/Icon";
import type { ProductAudience } from "@/lib/data";

const femaleItems: { icon: IconName; label: string; detail: string }[] = [
  { icon: "badgePercent", label: "5% OFF no site", detail: "Sobre o preço da tabela" },
  { icon: "sparkles", label: "Cera em primeiro", detail: "O carro-chefe da marca" },
  { icon: "clock", label: "Sem agendamento", detail: "Atendimento por ordem de chegada" },
  { icon: "shieldCheck", label: "Compra segura", detail: "Cartão protegido" },
  { icon: "heart", label: "Cortesia de primeira vez", detail: "Na unidade escolhida" },
  { icon: "scanFace", label: "Atendimento feminino", detail: "Ambiente exclusivo" },
  { icon: "star", label: "Laser e cera", detail: "Tudo na mesma loja" },
  { icon: "house", label: "Unidades no RJ e SP", detail: "Loja perto de você" },
  { icon: "check", label: "Avaliação com especialista", detail: "Pacotes a laser" },
];

const maleItems: { icon: IconName; label: string; detail: string }[] = [
  { icon: "badgePercent", label: "5% OFF no site", detail: "Sobre o preço da tabela" },
  { icon: "sparkles", label: "Cera em primeiro", detail: "Peito, costas e corpo" },
  { icon: "clock", label: "Sem agendamento", detail: "Atendimento por ordem de chegada" },
  { icon: "shieldCheck", label: "Compra segura", detail: "Cartão protegido" },
  { icon: "scanFace", label: "Atendimento masculino", detail: "Unidades selecionadas" },
  { icon: "star", label: "Cera e laser", detail: "Tudo na mesma loja" },
  { icon: "house", label: "Unidades no RJ e SP", detail: "Loja perto de você" },
  { icon: "check", label: "Avaliação com especialista", detail: "Pacotes a laser" },
];

function Row({
  suffix,
  items,
}: {
  suffix: string;
  items: { icon: IconName; label: string; detail: string }[];
}) {
  return (
    <ul className="flex shrink-0 items-center gap-8 px-4" aria-hidden={suffix !== "a"}>
      {items.map((item) => (
        <li
          key={`${suffix}-${item.label}`}
          className="flex shrink-0 items-center gap-2.5 whitespace-nowrap"
        >
          <Icon name={item.icon} size={15} className="text-secondary-container" />
          <span className="text-[12px] font-semibold tracking-wide text-white uppercase">
            {item.label}
          </span>
          <span className="text-[12px] text-white/70">{item.detail}</span>
          <span className="ml-6 text-secondary-container" aria-hidden>
            •
          </span>
        </li>
      ))}
    </ul>
  );
}

type Props = {
  audience?: ProductAudience;
};

export function TrustBar({ audience = "feminino" }: Props) {
  const items = audience === "masculino" ? maleItems : femaleItems;
  return (
    <div className="overflow-hidden border-b border-white/10 bg-primary py-2.5">
      <div className="benefits-marquee flex w-max">
        <Row suffix="a" items={items} />
        <Row suffix="b" items={items} />
      </div>
    </div>
  );
}

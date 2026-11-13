import { readFileSync } from "fs";
import { join } from "path";
import { LegalPage } from "@/components/LegalPage";

export default function TermosPage() {
  const html = readFileSync(
    join(process.cwd(), "src/content/termos-condicoes.html"),
    "utf8",
  );

  return (
    <LegalPage title="Termos e Condições">
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </LegalPage>
  );
}

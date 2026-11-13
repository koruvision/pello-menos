import { readFileSync } from "fs";
import { join } from "path";
import { LegalPage } from "@/components/LegalPage";

export default function PrivacidadePage() {
  const html = readFileSync(
    join(process.cwd(), "src/content/politica-privacidade.html"),
    "utf8",
  );

  return (
    <LegalPage title="POLÍTICA DE PRIVACIDADE E DE SEGURANÇA DAS INFORMAÇÕES">
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </LegalPage>
  );
}

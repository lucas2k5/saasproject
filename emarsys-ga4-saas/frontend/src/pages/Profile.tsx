import DashboardLayout from "../components/DashboardLayout";
import { useAuth } from "../context/AuthContext";

function Profile() {
  const { user } = useAuth();
  const metadata = user?.user_metadata as Record<string, unknown> | undefined;
  const fullName = typeof metadata?.full_name === "string" ? metadata.full_name : "";
  const companyName =
    typeof metadata?.company_name === "string" ? metadata.company_name : "";
  const phone = typeof metadata?.phone === "string" ? metadata.phone : "";
  const marketingOptIn =
    typeof metadata?.marketing_opt_in === "boolean" ? metadata.marketing_opt_in : null;

  return (
    <DashboardLayout
      title="Perfil"
      subtitle="Informações da conta e preferências"
      label="Perfil do usuário"
    >
      <section className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">Dados pessoais</h2>
          <div className="mt-6 grid gap-4 text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                Nome completo
              </p>
              <p className="mt-1 text-[color:var(--ink)]">{fullName || "Não informado"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                E-mail
              </p>
              <p className="mt-1 text-[color:var(--ink)]">{user?.email ?? "Não informado"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                Telefone
              </p>
              <p className="mt-1 text-[color:var(--ink)]">{phone || "Não informado"}</p>
            </div>
          </div>
        </article>

        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">
            Informações da empresa
          </h2>
          <div className="mt-6 grid gap-4 text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                Empresa
              </p>
              <p className="mt-1 text-[color:var(--ink)]">{companyName || "Não informado"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                Preferência LGPD
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {marketingOptIn === null
                  ? "Não informado"
                  : marketingOptIn
                    ? "Opt-in (aceita comunicações)"
                    : "Opt-out (não aceita comunicações)"}
              </p>
            </div>
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Profile;

"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Icon } from "@/components/Icon";
import { useStore } from "@/components/StoreProvider";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function AuthModal({ open, onClose }: Props) {
  const { user, login, register, logout } = useStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    setBusy(false);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    const message =
      mode === "login"
        ? login(email, password)
        : register(name, email, password, phone);
    if (message) {
      setError(message);
      setBusy(false);
      return;
    }
    setName("");
    setPhone("");
    setEmail("");
    setPassword("");
    setBusy(false);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-[75] flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        className="absolute inset-0 bg-black/60"
        aria-label="Fechar conta"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
        className="pm-account-card relative w-full max-w-md p-6"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-white/70 hover:text-[#e8b86d]"
          aria-label="Fechar"
        >
          <Icon name="close" size={20} />
        </button>

        {user ? (
          <div>
            <p className="font-label-md text-label-md uppercase tracking-[0.18em] text-[#e8b86d]">
              Minha conta
            </p>
            <h2
              id="auth-title"
              className="mt-2 font-[family-name:var(--font-display)] text-3xl text-white"
            >
              Olá, {user.name}
            </h2>
            <p className="mt-1 text-sm text-white/70">{user.email}</p>
            <div className="mt-5 h-px bg-gradient-to-r from-transparent via-[#e8b86d]/55 to-transparent" />
            <button
              type="button"
              onClick={() => {
                logout();
                onClose();
              }}
              className="btn-lux btn-lux-ghost mt-6 w-full rounded-full border border-[#e8b86d]/45 px-4 py-3 text-sm font-semibold text-[#e8b86d] uppercase"
            >
              Sair
            </button>
          </div>
        ) : (
          <>
            <p className="font-label-md text-label-md uppercase tracking-[0.18em] text-[#e8b86d]">
              Minha conta
            </p>
            <h2
              id="auth-title"
              className="mt-2 pr-8 font-[family-name:var(--font-display)] text-3xl text-white"
            >
              {mode === "login" ? "Entrar" : "Criar conta"}
            </h2>
            <p className="mt-1 text-sm text-white/70">
              {mode === "login"
                ? "Acesse para acompanhar pedidos e ofertas."
                : "Cadastre-se para comprar mais rápido."}
            </p>
            <div className="mt-5 grid grid-cols-2 gap-2 rounded-full border border-white/15 bg-white/10 p-1">
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
                className={
                  mode === "login"
                    ? "btn-lux btn-lux-gold rounded-full py-2 text-sm font-semibold text-on-secondary-container"
                    : "rounded-full py-2 text-sm text-white/70"
                }
              >
                Entrar
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("register");
                  setError("");
                }}
                className={
                  mode === "register"
                    ? "btn-lux btn-lux-gold rounded-full py-2 text-sm font-semibold text-on-secondary-container"
                    : "rounded-full py-2 text-sm text-white/70"
                }
              >
                Cadastrar
              </button>
            </div>
            <form onSubmit={submit} className="mt-5 space-y-3">
              {mode === "register" ? (
                <>
                  <label className="block text-sm text-white/85">
                    Nome
                    <input
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      className="mt-1 w-full rounded-2xl border border-white/20 bg-white/8 px-4 py-3 text-white outline-none focus:border-[#e8b86d]"
                      autoComplete="name"
                      required
                    />
                  </label>
                  <label className="block text-sm text-white/85">
                    Telefone
                    <input
                      type="tel"
                      inputMode="tel"
                      value={phone}
                      onChange={(event) => setPhone(event.target.value)}
                      className="mt-1 w-full rounded-2xl border border-white/20 bg-white/8 px-4 py-3 text-white outline-none focus:border-[#e8b86d]"
                      autoComplete="tel"
                      required
                    />
                  </label>
                </>
              ) : null}
              <label className="block text-sm text-white/85">
                E-mail
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="mt-1 w-full rounded-2xl border border-white/20 bg-white/8 px-4 py-3 text-white outline-none focus:border-[#e8b86d]"
                  autoComplete="email"
                  required
                />
              </label>
              <label className="block text-sm text-white/85">
                Senha
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="mt-1 w-full rounded-2xl border border-white/20 bg-white/8 px-4 py-3 text-white outline-none focus:border-[#e8b86d]"
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  required
                />
              </label>
              {error ? (
                <p className="text-sm text-[#e8b86d]">{error}</p>
              ) : null}
              <button
                type="submit"
                disabled={busy}
                className="btn-lux btn-lux-gold inline-flex w-full items-center justify-center gap-2 rounded-full py-3 text-sm font-semibold tracking-wide text-on-secondary-container uppercase disabled:opacity-80"
              >
                {busy ? (
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                    fill="none"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeOpacity="0.25"
                      strokeWidth="3"
                    />
                    <path
                      d="M22 12a10 10 0 0 1-10 10"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : null}
                {busy
                  ? mode === "login"
                    ? "Entrando…"
                    : "Cadastrando…"
                  : mode === "login"
                    ? "Entrar"
                    : "Criar conta"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

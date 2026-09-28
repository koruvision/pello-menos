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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  function submit(event: FormEvent) {
    event.preventDefault();
    const message =
      mode === "login"
        ? login(email, password)
        : register(name, email, password);
    if (message) {
      setError(message);
      return;
    }
    setName("");
    setEmail("");
    setPassword("");
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
        className="relative w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-on-surface-variant hover:text-primary"
          aria-label="Fechar"
        >
          <Icon name="close" size={20} />
        </button>

        {user ? (
          <div>
            <p className="font-label-md text-label-md text-primary uppercase">
              Minha conta
            </p>
            <h2
              id="auth-title"
              className="mt-2 font-[family-name:var(--font-display)] text-3xl text-primary"
            >
              Olá, {user.name}
            </h2>
            <p className="mt-1 text-sm text-on-surface-variant">{user.email}</p>
            <button
              type="button"
              onClick={() => {
                logout();
                onClose();
              }}
              className="btn-lux btn-lux-ghost mt-6 w-full rounded-full border border-primary px-4 py-3 text-sm font-semibold text-primary uppercase"
            >
              Sair
            </button>
          </div>
        ) : (
          <>
            <h2
              id="auth-title"
              className="pr-8 font-[family-name:var(--font-display)] text-3xl text-primary"
            >
              {mode === "login" ? "Entrar" : "Criar conta"}
            </h2>
            <p className="mt-1 text-sm text-on-surface-variant">
              {mode === "login"
                ? "Acesse para acompanhar pedidos e ofertas."
                : "Cadastre-se para comprar mais rápido."}
            </p>
            <div className="mt-5 grid grid-cols-2 gap-2 rounded-full bg-surface-container-low p-1">
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
                className={
                  mode === "login"
                    ? "btn-lux btn-lux-primary rounded-full py-2 text-sm font-semibold text-white"
                    : "rounded-full py-2 text-sm text-on-surface-variant"
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
                    ? "btn-lux btn-lux-primary rounded-full py-2 text-sm font-semibold text-white"
                    : "rounded-full py-2 text-sm text-on-surface-variant"
                }
              >
                Cadastrar
              </button>
            </div>
            <form onSubmit={submit} className="mt-5 space-y-3">
              {mode === "register" ? (
                <label className="block text-sm">
                  Nome
                  <input
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    className="mt-1 w-full rounded-2xl border border-outline/50 px-4 py-3 outline-none focus:border-primary"
                    autoComplete="name"
                  />
                </label>
              ) : null}
              <label className="block text-sm">
                E-mail
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="mt-1 w-full rounded-2xl border border-outline/50 px-4 py-3 outline-none focus:border-primary"
                  autoComplete="email"
                />
              </label>
              <label className="block text-sm">
                Senha
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="mt-1 w-full rounded-2xl border border-outline/50 px-4 py-3 outline-none focus:border-primary"
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                />
              </label>
              {error ? (
                <p className="text-sm text-primary">{error}</p>
              ) : null}
              <button
                type="submit"
                className="btn-lux btn-lux-primary w-full rounded-full py-3 text-sm font-semibold tracking-wide text-white uppercase"
              >
                {mode === "login" ? "Entrar" : "Criar conta"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

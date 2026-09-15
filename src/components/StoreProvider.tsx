"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { Product, StoreUnit } from "@/lib/data";

export type CartItem = {
  lineId: string;
  product: Product;
  unit: StoreUnit;
  qty: number;
};

function cartLineId(productId: string, unitId: string) {
  return `${productId}::${unitId}`;
}

type Toast = { id: number; message: string } | null;

export type UserAccount = {
  name: string;
  email: string;
};

type StoreContextValue = {
  cartItems: CartItem[];
  cartCount: number;
  subtotalCents: number;
  toast: Toast;
  user: UserAccount | null;
  addToCart: (product: Product, unit: StoreUnit, qty?: number) => boolean;
  removeFromCart: (lineId: string) => void;
  setQty: (lineId: string, qty: number) => void;
  setAllQty: (qty: number) => void;
  clearCart: () => void;
  login: (email: string, password: string) => string | null;
  register: (name: string, email: string, password: string) => string | null;
  logout: () => void;
};

const USER_KEY = "pello-menos-user";
const ACCOUNTS_KEY = "pello-menos-accounts";

const StoreContext = createContext<StoreContextValue | null>(null);

function readAccounts(): Array<UserAccount & { password: string }> {
  try {
    return JSON.parse(localStorage.getItem(ACCOUNTS_KEY) || "[]");
  } catch {
    return [];
  }
}

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [toast, setToast] = useState<Toast>(null);
  const [user, setUser] = useState<UserAccount | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(USER_KEY);
      if (saved) setUser(JSON.parse(saved) as UserAccount);
    } catch {
      localStorage.removeItem(USER_KEY);
    }
  }, []);

  const showToast = useCallback((message: string) => {
    const id = Date.now();
    setToast({ id, message });
    window.setTimeout(() => {
      setToast((current) => (current?.id === id ? null : current));
    }, 3500);
  }, []);

  const addToCart = useCallback(
    (product: Product, unit: StoreUnit, qty = 1) => {
      const locked = cartItems[0]?.unit;
      if (locked && locked.id !== unit.id) {
        showToast(
          `O carrinho é da unidade ${locked.name}. Esvazie ou finalize para comprar em ${unit.name}.`,
        );
        return false;
      }
      const lineId = cartLineId(product.id, unit.id);
      const amount = Math.max(1, qty);
      setCartItems((current) => {
        const existing = current.find((item) => item.lineId === lineId);
        if (existing) {
          return current.map((item) =>
            item.lineId === lineId
              ? { ...item, qty: item.qty + amount }
              : item,
          );
        }
        return [...current, { lineId, product, unit, qty: amount }];
      });
      showToast(`${product.name} adicionado · ${unit.name}`);
      return true;
    },
    [cartItems, showToast],
  );

  const clearCart = useCallback(() => {
    setCartItems([]);
    showToast("Carrinho esvaziado");
  }, [showToast]);

  const removeFromCart = useCallback((lineId: string) => {
    setCartItems((current) =>
      current.filter((item) => item.lineId !== lineId),
    );
  }, []);

  const setQty = useCallback((lineId: string, qty: number) => {
    setCartItems((current) => {
      if (qty < 1) {
        return current.filter((item) => item.lineId !== lineId);
      }
      return current.map((item) =>
        item.lineId === lineId ? { ...item, qty } : item,
      );
    });
  }, []);

  const setAllQty = useCallback((qty: number) => {
    const next = Math.max(1, Math.floor(qty) || 1);
    setCartItems((current) =>
      current.map((item) => ({ ...item, qty: next })),
    );
  }, []);

  const login = useCallback(
    (email: string, password: string) => {
      const cleanEmail = email.trim().toLowerCase();
      if (!cleanEmail || !password) return "Preencha e-mail e senha.";
      const match = readAccounts().find(
        (account) => account.email === cleanEmail && account.password === password,
      );
      if (!match) return "E-mail ou senha incorretos.";
      const next = { name: match.name, email: match.email };
      setUser(next);
      localStorage.setItem(USER_KEY, JSON.stringify(next));
      showToast(`Olá, ${next.name}`);
      return null;
    },
    [showToast],
  );

  const register = useCallback(
    (name: string, email: string, password: string) => {
      const cleanName = name.trim();
      const cleanEmail = email.trim().toLowerCase();
      if (!cleanName || !cleanEmail || !password) {
        return "Preencha nome, e-mail e senha.";
      }
      if (password.length < 6) return "A senha precisa ter pelo menos 6 caracteres.";
      const accounts = readAccounts();
      if (accounts.some((account) => account.email === cleanEmail)) {
        return "Esse e-mail já tem conta.";
      }
      const next = { name: cleanName, email: cleanEmail };
      localStorage.setItem(
        ACCOUNTS_KEY,
        JSON.stringify([...accounts, { ...next, password }]),
      );
      setUser(next);
      localStorage.setItem(USER_KEY, JSON.stringify(next));
      showToast("Conta criada");
      return null;
    },
    [showToast],
  );

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem(USER_KEY);
    showToast("Você saiu da conta");
  }, [showToast]);

  const value = useMemo(() => {
    const cartCount = cartItems.reduce((sum, item) => sum + item.qty, 0);
    const subtotalCents = cartItems.reduce(
      (sum, item) => sum + item.product.priceCents * item.qty,
      0,
    );
    return {
      cartItems,
      cartCount,
      subtotalCents,
      toast,
      user,
      addToCart,
      removeFromCart,
      setQty,
      setAllQty,
      clearCart,
      login,
      register,
      logout,
    };
  }, [
    cartItems,
    toast,
    user,
    addToCart,
    removeFromCart,
    setQty,
    setAllQty,
    clearCart,
    login,
    register,
    logout,
  ]);

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const context = useContext(StoreContext);
  if (!context) {
    throw new Error("useStore precisa estar dentro de StoreProvider");
  }
  return context;
}

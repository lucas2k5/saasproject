import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { supabaseClient } from "../lib/supabaseClient";
import { translations, type Locale } from "../i18n/translations";
import { useAuth } from "./AuthContext";

type LocaleContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => Promise<void>;
  t: (key: string) => string;
};

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);
const storageKey = "keepais:locale";

export function LocaleProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [locale, setLocaleState] = useState<Locale>("pt-BR");

  useEffect(() => {
    const stored = localStorage.getItem(storageKey);
    if (stored === "pt-BR" || stored === "en-US") {
      setLocaleState(stored);
    }
  }, []);

  useEffect(() => {
    const metadataLocale = user?.user_metadata?.language;
    if (metadataLocale === "pt-BR" || metadataLocale === "en-US") {
      setLocaleState(metadataLocale);
      localStorage.setItem(storageKey, metadataLocale);
    }
  }, [user]);

  const setLocale = async (nextLocale: Locale) => {
    setLocaleState(nextLocale);
    localStorage.setItem(storageKey, nextLocale);

    if (supabaseClient && user) {
      await supabaseClient.auth.updateUser({
        data: {
          language: nextLocale
        }
      });
    }
  };

  const t = useMemo(() => {
    return (key: string) => translations[locale][key] ?? key;
  }, [locale]);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useLocale must be used within LocaleProvider");
  }
  return context;
}

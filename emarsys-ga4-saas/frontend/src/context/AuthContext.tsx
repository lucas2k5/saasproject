import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabaseClient, supabaseConfigError } from "../lib/supabaseClient";

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
  hasSupabaseConfig: boolean;
  signIn: (email: string, password: string) => Promise<string | null>;
  signUp: (payload: {
    fullName: string;
    email: string;
    password: string;
    phone: string;
    companyName: string;
    marketingOptIn: boolean;
  }) => Promise<string | null>;
  signInWithGoogle: () => Promise<string | null>;
  signOut: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(supabaseConfigError);

  useEffect(() => {
    if (!supabaseClient) {
      setLoading(false);
      return;
    }

    supabaseClient.auth.getSession().then(({ data, error: sessionError }) => {
      if (sessionError) {
        setError(sessionError.message);
      }
      setSession(data.session ?? null);
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const { data } = supabaseClient.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      data.subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    if (!supabaseClient) {
      return "Supabase não configurado. Preencha as variáveis de ambiente.";
    }

    const { error } = await supabaseClient.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
      return error.message;
    }

    setError(null);
    return null;
  };

  const signUp = async ({
    fullName,
    email,
    password,
    phone,
    companyName,
    marketingOptIn
  }: {
    fullName: string;
    email: string;
    password: string;
    phone: string;
    companyName: string;
    marketingOptIn: boolean;
  }) => {
    if (!supabaseClient) {
      return "Supabase não configurado. Preencha as variáveis de ambiente.";
    }

    const { error } = await supabaseClient.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          phone,
          company_name: companyName,
          marketing_opt_in: marketingOptIn
        }
      }
    });

    if (error) {
      setError(error.message);
      return error.message;
    }

    setError(null);
    return null;
  };

  const signInWithGoogle = async () => {
    if (!supabaseClient) {
      return "Supabase não configurado. Preencha as variáveis de ambiente.";
    }

    const { error } = await supabaseClient.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/dashboard`
      }
    });

    if (error) {
      setError(error.message);
      return error.message;
    }

    setError(null);
    return null;
  };

  const signOut = async () => {
    if (!supabaseClient) {
      return "Supabase não configurado. Preencha as variáveis de ambiente.";
    }

    const { error } = await supabaseClient.auth.signOut();
    if (error) {
      setError(error.message);
      return error.message;
    }

    setError(null);
    return null;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        error,
        hasSupabaseConfig: !supabaseConfigError,
        signIn,
        signUp,
        signInWithGoogle,
        signOut
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

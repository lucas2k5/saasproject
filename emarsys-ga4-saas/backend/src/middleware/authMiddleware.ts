import type { NextFunction, Request, Response } from "express";
import { supabaseAdmin, supabaseConfigError } from "../lib/supabaseAdmin";

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  if (process.env.AUTH_DISABLED === "true") {
    req.user = { id: "dev-user", email: "dev@keepais.local" };
    return next();
  }

  const authHeader = req.headers.authorization;

  if (!supabaseAdmin) {
    return res.status(500).json({ error: supabaseConfigError ?? "Supabase not configured" });
  }

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing Authorization header" });
  }

  const token = authHeader.replace("Bearer ", "").trim();
  if (!token) {
    return res.status(401).json({ error: "Invalid token" });
  }

  const { data, error } = await supabaseAdmin.auth.getUser(token);
  if (error || !data.user) {
    return res.status(401).json({ error: "Invalid or expired token" });
  }

  req.user = { id: data.user.id, email: data.user.email ?? undefined };
  return next();
}

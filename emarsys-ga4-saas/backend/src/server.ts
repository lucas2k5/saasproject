import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import reportsRouter from "./routes/reports";
import { authMiddleware } from "./middleware/authMiddleware";
import mlRouter from "./routes/ml";

dotenv.config();

const app = express();
const corsOrigins =
  process.env.CORS_ORIGIN?.split(",").map((origin) => origin.trim()) ?? [
    "http://localhost:5173"
  ];

app.use(
  cors({
    origin: corsOrigins,
    credentials: true
  })
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.get("/api/me", authMiddleware, (req, res) => {
  res.json({ user: req.user ?? null });
});

app.use("/api/reports", authMiddleware, reportsRouter);
app.use("/api/ml", authMiddleware, mlRouter);

const port = Number(process.env.PORT) || 3001;
app.listen(port, () => {
  console.log(`Backend listening on http://localhost:${port}`);
});

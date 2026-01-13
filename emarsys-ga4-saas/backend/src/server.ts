import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import reportsRouter from "./routes/reports";
import { authMiddleware } from "./middleware/authMiddleware";
import mlRouter from "./routes/ml";
import path from "path";
import swaggerUi from "swagger-ui-express";
import yaml from "yamljs";

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

const docsBasePath = path.join(__dirname, "..", "docs");
const coreSpec = yaml.load(path.join(docsBasePath, "openapi-core.yaml"));
const emarsysSpec = yaml.load(path.join(docsBasePath, "openapi-emarsys.yaml"));
const ga4Spec = yaml.load(path.join(docsBasePath, "openapi-ga4.yaml"));
const vtexSpec = yaml.load(path.join(docsBasePath, "openapi-vtex.yaml"));
const hubspotSpec = yaml.load(path.join(docsBasePath, "openapi-hubspot.yaml"));
const klaviyoSpec = yaml.load(path.join(docsBasePath, "openapi-klaviyo.yaml"));
const sfmcSpec = yaml.load(path.join(docsBasePath, "openapi-sfmc.yaml"));

app.use("/docs", swaggerUi.serve, swaggerUi.setup(coreSpec));
app.use("/docs/emarsys", swaggerUi.serve, swaggerUi.setup(emarsysSpec));
app.use("/docs/ga4", swaggerUi.serve, swaggerUi.setup(ga4Spec));
app.use("/docs/vtex", swaggerUi.serve, swaggerUi.setup(vtexSpec));
app.use("/docs/hubspot", swaggerUi.serve, swaggerUi.setup(hubspotSpec));
app.use("/docs/klaviyo", swaggerUi.serve, swaggerUi.setup(klaviyoSpec));
app.use("/docs/sfmc", swaggerUi.serve, swaggerUi.setup(sfmcSpec));

app.use("/api/reports", authMiddleware, reportsRouter);
app.use("/api/ml", authMiddleware, mlRouter);

const port = Number(process.env.PORT) || 3001;
app.listen(port, () => {
  console.log(`Backend listening on http://localhost:${port}`);
});

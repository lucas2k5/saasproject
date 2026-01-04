import { Router } from "express";
import { emarsysReport } from "../mocks/emarsys";
import { ga4Report } from "../mocks/ga4";
import { combinedReport } from "../mocks/combined";

const router = Router();

router.get("/emarsys", (_req, res) => {
  res.json(emarsysReport);
});

router.get("/ga4", (_req, res) => {
  res.json(ga4Report);
});

router.get("/combined", (_req, res) => {
  res.json(combinedReport);
});

export default router;

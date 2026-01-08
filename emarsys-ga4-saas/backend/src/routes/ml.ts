import { Router } from "express";
import { predictEngagement } from "../services/mlService";

const router = Router();

router.post("/engagement", async (req, res) => {
  const { customerId, features } = req.body as {
    customerId?: string;
    features?: Record<string, unknown>;
  };

  if (!customerId || !features) {
    return res.status(400).json({ error: "customerId and features are required" });
  }

  try {
    const prediction = await predictEngagement({ customerId, features });
    return res.json(prediction);
  } catch (error) {
    return res.status(502).json({ error: "Failed to reach ML service" });
  }
});

export default router;

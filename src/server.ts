import express from "express";
import { config } from "./config";
import scoresRouter from "./routes/scores";
import { errorHandler } from "./middleware/errorHandler";

const app = express();

app.use(express.json());

// Routes
app.use("/api/v1", scoresRouter);

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// Error handler
app.use(errorHandler);

app.listen(config.port, () => {
  console.log(`Upscale Score Engine running on port ${config.port}`);
});

export default app;

import "dotenv/config";
import express from "express";
import mongoose from "mongoose";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const app = express();
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const modelServiceUrl = process.env.MODEL_SERVICE_URL?.replace(/\/$/, "");

app.disable("x-powered-by");
app.use(express.json({ limit: "32kb" }));

let mongoConnection;
const watchlistSchema = new mongoose.Schema({
  visitorId: { type: String, required: true, unique: true, index: true },
  playerIds: { type: [String], default: [] },
  updatedAt: { type: Date, default: Date.now },
});
const Watchlist = mongoose.models.Watchlist || mongoose.model("Watchlist", watchlistSchema);

async function connectMongo() {
  if (!process.env.MONGODB_URI) throw new Error("Watchlist storage is not configured yet.");
  if (mongoose.connection.readyState === 1) return;
  if (!mongoConnection) {
    mongoConnection = mongoose.connect(process.env.MONGODB_URI, {
      serverSelectionTimeoutMS: 6000,
      maxPoolSize: 5,
    }).catch((error) => {
      mongoConnection = undefined;
      throw error;
    });
  }
  await mongoConnection;
}

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", modelService: Boolean(modelServiceUrl) });
});

app.get("/api/watchlist/:visitorId", async (req, res) => {
  if (!/^[a-f0-9-]{36}$/i.test(req.params.visitorId)) {
    return res.status(400).json({ error: "Invalid visitor id." });
  }
  try {
    await connectMongo();
    const list = await Watchlist.findOne({ visitorId: req.params.visitorId }).lean();
    res.json({ playerIds: list?.playerIds ?? [] });
  } catch (error) {
    res.status(503).json({ error: error.message || "Watchlist storage is unavailable." });
  }
});

app.put("/api/watchlist/:visitorId", async (req, res) => {
  if (!/^[a-f0-9-]{36}$/i.test(req.params.visitorId)) {
    return res.status(400).json({ error: "Invalid visitor id." });
  }
  const playerIds = Array.isArray(req.body?.playerIds)
    ? [...new Set(req.body.playerIds.filter((id) => typeof id === "string"))].slice(0, 200)
    : null;
  if (!playerIds) return res.status(400).json({ error: "playerIds must be an array." });
  try {
    await connectMongo();
    await Watchlist.findOneAndUpdate(
      { visitorId: req.params.visitorId },
      { $set: { playerIds, updatedAt: new Date() } },
      { upsert: true, new: true, setDefaultsOnInsert: true },
    );
    res.json({ playerIds });
  } catch (error) {
    res.status(503).json({ error: error.message || "Watchlist storage is unavailable." });
  }
});

app.use("/api", async (req, res) => {
  if (!modelServiceUrl) {
    return res.status(503).json({ error: "Set MODEL_SERVICE_URL to connect the Python model service." });
  }
  try {
    const response = await fetch(`${modelServiceUrl}${req.path}${req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : ""}`, {
      method: req.method,
      headers: { "content-type": "application/json" },
      body: ["GET", "HEAD"].includes(req.method) ? undefined : JSON.stringify(req.body ?? {}),
      signal: AbortSignal.timeout(100_000),
    });
    const body = await response.text();
    res.status(response.status).type(response.headers.get("content-type") || "application/json").send(body);
  } catch (error) {
    res.status(502).json({ error: "The player model service could not be reached.", detail: error.message });
  }
});

app.use((error, _req, res, _next) => {
  console.error(error);
  res.status(500).json({ error: "Unexpected server error." });
});

if (process.env.NODE_ENV !== "production" && process.env.VERCEL !== "1") {
  const port = process.env.PORT || 4100;
  app.listen(port, () => console.log(`ScoutIQ API listening on ${port}`));
}

export default app;

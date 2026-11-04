// Explicit profile route avoids ambiguous catch-all routing for nested player URLs.
export default async function playerProfile(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    return res.status(405).json({ error: "Method not allowed." });
  }

  const modelServiceUrl = process.env.MODEL_SERVICE_URL?.replace(/\/$/, "");
  if (!modelServiceUrl) {
    return res.status(503).json({ error: "Set MODEL_SERVICE_URL to connect the Python model service." });
  }

  const playerId = req.query?.playerId;
  if (typeof playerId !== "string" || !playerId) {
    return res.status(400).json({ error: "A player ID is required." });
  }

  try {
    const response = await fetch(`${modelServiceUrl}/players/${encodeURIComponent(playerId)}`, {
      method: "GET",
      signal: AbortSignal.timeout(100_000),
    });
    const body = await response.text();
    res.status(response.status).type(response.headers.get("content-type") || "application/json").send(body);
  } catch (error) {
    res.status(502).json({ error: "The player model service could not be reached.", detail: error.message });
  }
}

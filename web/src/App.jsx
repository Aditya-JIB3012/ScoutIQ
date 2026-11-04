import { useCallback, useEffect, useState } from "react";
import {
  Activity, ArrowRight, ArrowUpRight, BarChart3, Bookmark,
  Check, ChevronDown, ChevronLeft, ChevronRight, CircleHelp, Clock3, Compass,
  Filter, Gauge, LayoutDashboard, LoaderCircle, Moon, Search, Settings2, Shield,
  SlidersHorizontal, Sparkles, Star, Sun, Target, TrendingUp, Users, X,
} from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, PolarAngleAxis, PolarGrid, Radar,
  RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "./api.js";

const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "players", label: "Player database", icon: Users },
  { id: "value", label: "Value finder", icon: Target },
  { id: "compare", label: "Compare players", icon: Activity },
  { id: "simulator", label: "Value simulator", icon: SlidersHorizontal },
  { id: "diagnostics", label: "Model diagnostics", icon: BarChart3 },
];
const money = (value, decimals = 1) => `€${Number(value || 0).toFixed(decimals)}M`;
const shortMoney = (value) => `€${Number(value || 0).toFixed(0)}m`;
const titleCase = (value = "") => /^la\s?liga$/i.test(value.trim()) ? "LaLiga" : value.toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

function getVisitorId() {
  let id = localStorage.getItem("scoutiq-visitor");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("scoutiq-visitor", id);
  }
  return id;
}

function App() {
  const [page, setPage] = useState("overview");
  const [theme, setTheme] = useState(() => localStorage.getItem("scoutiq-theme") === "dark" ? "dark" : "light");
  const [metadata, setMetadata] = useState(null);
  const [players, setPlayers] = useState([]);
  const [topPlayers, setTopPlayers] = useState([]);
  const [playerTotal, setPlayerTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [league, setLeague] = useState("");
  const [role, setRole] = useState("");
  const [maxAge, setMaxAge] = useState("");
  const [maxValue, setMaxValue] = useState("");
  const [sort, setSort] = useState("value");
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [activePlayerId, setActivePlayerId] = useState("");
  const [profile, setProfile] = useState(null);
  const [watchlist, setWatchlist] = useState(() => JSON.parse(localStorage.getItem("scoutiq-watchlist") || "[]"));
  const [watchlistStored, setWatchlistStored] = useState(false);
  const [visitorId] = useState(getVisitorId);
  const [budget, setBudget] = useState(45);
  const [under24, setUnder24] = useState(true);
  const [deals, setDeals] = useState([]);
  const [dealCount, setDealCount] = useState(0);
  const [firstId, setFirstId] = useState("");
  const [secondId, setSecondId] = useState("");
  const [comparison, setComparison] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [simulationId, setSimulationId] = useState("");
  const [simulation, setSimulation] = useState(null);
  const [simInputs, setSimInputs] = useState(null);
  const [simBusy, setSimBusy] = useState(false);

  useEffect(() => {
    localStorage.setItem("scoutiq-theme", theme);
  }, [theme]);

  useEffect(() => {
    api.metadata().then((data) => {
      setMetadata(data);
      setError("");
    }).catch((err) => setError(err.message));
    api.players("sort=performance&order=desc&limit=6").then((data) => setTopPlayers(data.items)).catch(() => {});
    api.getWatchlist(visitorId).then((data) => {
      setWatchlist(data.playerIds || []);
      setWatchlistStored(true);
    }).catch(() => setWatchlistStored(false));
  }, [visitorId]);

  const loadPlayers = useCallback(async (reset = false) => {
    setBusy(true);
    const params = new URLSearchParams({
      search, league, role, sort, max_age: maxAge || "45", max_value: maxValue || "250", limit: "80", offset: String(reset ? 0 : offset),
    });
    try {
      const data = await api.players(params.toString());
      setPlayers(data.items);
      setPlayerTotal(data.total);
      setError("");
      if (!firstId && data.items.length) setFirstId(data.items[0].player_id);
      if (!secondId && data.items.length > 1) setSecondId(data.items[1].player_id);
      if (!simulationId && data.items.length) {
        const starter = data.items[0];
        setSimulationId(starter.player_id);
        setSimInputs({
          age: starter.age, ovr: starter.ovr, pot: starter.pot, pace: starter.pace,
          shooting: starter.shooting, passing: starter.passing, dribbling: starter.dribbling,
          defending: starter.defending, physical: starter.physical,
          goals_p90: starter.goals_p90, assists_p90: starter.assists_p90,
          contract_years_left: starter.contract_years_left, league: starter.league,
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }, [search, league, role, maxAge, maxValue, sort, offset, firstId, secondId, simulationId]);

  useEffect(() => {
    const timer = setTimeout(() => loadPlayers(), 280);
    return () => clearTimeout(timer);
  }, [loadPlayers]);

  useEffect(() => {
    localStorage.setItem("scoutiq-watchlist", JSON.stringify(watchlist));
    if (watchlistStored) api.saveWatchlist(visitorId, watchlist).catch(() => setWatchlistStored(false));
  }, [watchlist, visitorId, watchlistStored]);

  useEffect(() => {
    if (page === "value") {
      api.opportunities(budget, under24).then((data) => {
        setDeals(data.items);
        setDealCount(data.total);
      }).catch((err) => setError(err.message));
    }
  }, [page, budget, under24]);

  useEffect(() => {
    if (page === "compare" && firstId && secondId && firstId !== secondId) {
      api.compare(firstId, secondId).then((data) => setComparison(data.players)).catch((err) => setError(err.message));
    }
  }, [page, firstId, secondId]);

  useEffect(() => {
    if (["overview", "diagnostics"].includes(page) && !analytics) api.analytics().then(setAnalytics).catch(() => {});
  }, [page, analytics]);

  useEffect(() => {
    if (page === "report" && activePlayerId) {
      setProfile(null);
      api.player(activePlayerId).then(setProfile).catch((err) => setError(err.message));
    }
  }, [page, activePlayerId]);

  const gotoPlayer = (playerId) => {
    setActivePlayerId(playerId);
    setPage("report");
  };
  const toggleWatch = (playerId) => setWatchlist((list) => list.includes(playerId)
    ? list.filter((id) => id !== playerId)
    : [playerId, ...list]);
  const nav = (id) => {
    setPage(id);
    if (id !== "report") setActivePlayerId("");
  };

  const pageTitle = {
    overview: "Overview", players: "Player database", value: "Value finder",
    compare: "Compare players", simulator: "Value simulator", report: "Player report", diagnostics: "Model diagnostics",
  }[page] || "Overview";

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <button className="brand" onClick={() => nav("overview")} aria-label="ScoutIQ home">
          <span className="brand-mark"><span></span><span></span><span></span></span>
          <span className="brand-name">scout<span>iq</span><small>PLAYER INTELLIGENCE</small></span>
        </button>
        <div className="sidebar-caption">WORKSPACE</div>
        <nav className="primary-nav">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${page === id || (id === "players" && page === "report") ? "active" : ""}`} onClick={() => nav(id)}>
              <Icon size={17} strokeWidth={1.8} /> <span>{label}</span>
              {id === "players" && watchlist.length > 0 && <b className="nav-count">{watchlist.length}</b>}
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-data-card">
          <span className="data-live-dot" />
          <div><b>Dataset connected</b><small>{metadata?.source || "Connecting to player data"}</small></div>
          <ChevronDown size={14} />
        </div>
        <div className="sidebar-footer">
          <div className="user-avatar">SQ</div>
          <div className="user-copy"><b>ScoutIQ workspace</b><small>Talent operations</small></div>
          <Settings2 size={16} />
        </div>
      </aside>

      <main className="main-shell">
        <header className="topbar">
          <div className="crumb"><span>SCOUTIQ</span><span className="crumb-slash">/</span><b>{pageTitle}</b></div>
          <div className="topbar-right">
            <div className="season-label"><span className="season-dot" />{metadata?.source || "Loading season data"}</div>
            <button className="icon-button theme-toggle" title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`} onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}</button>
            <button className="icon-button" title="Help"><CircleHelp size={17} /></button>
          </div>
        </header>

        <div className="page-content">
          {error && <div className="error-banner"><CircleHelp size={18} /><div><b>Couldn’t load ScoutIQ data</b><span>{error}</span><small>Start the Python model service and set MODEL_SERVICE_URL in the web app environment.</small></div><button onClick={() => { setError(""); loadPlayers(true); }}><ArrowRight size={16} /></button></div>}
          {page === "overview" && <Overview
            players={topPlayers} metadata={metadata} analytics={analytics} busy={busy} watchlist={watchlist}
            onOpen={gotoPlayer} onNavigate={nav} onWatch={toggleWatch}
          />}
          {page === "players" && <PlayerDirectory
            players={players} total={playerTotal} busy={busy} search={search} setSearch={(v) => { setSearch(v); setOffset(0); }}
            league={league} setLeague={(v) => { setLeague(v); setOffset(0); }} role={role} setRole={(v) => { setRole(v); setOffset(0); }}
            maxAge={maxAge} setMaxAge={(v) => { setMaxAge(v); setOffset(0); }} maxValue={maxValue} setMaxValue={(v) => { setMaxValue(v); setOffset(0); }}
            sort={sort} setSort={setSort} leagues={metadata?.leagues || []} roles={metadata?.roles || []}
            offset={offset} setOffset={setOffset} onOpen={gotoPlayer} watchlist={watchlist} onWatch={toggleWatch}
          />}
          {page === "report" && <PlayerReport
            profile={profile} loading={!profile} isSaved={watchlist.includes(activePlayerId)}
            onBack={() => nav("players")} onWatch={() => toggleWatch(activePlayerId)}
            onCompare={() => { setFirstId(activePlayerId); setPage("compare"); }}
          />}
          {page === "value" && <ValueFinder budget={budget} setBudget={setBudget} under24={under24} setUnder24={setUnder24} deals={deals} count={dealCount} loading={busy} onOpen={gotoPlayer} onWatch={toggleWatch} watchlist={watchlist} />}
          {page === "compare" && <ComparePage
            players={players} firstId={firstId} setFirstId={setFirstId} secondId={secondId} setSecondId={setSecondId} comparison={comparison} onOpen={gotoPlayer}
          />}
          {page === "simulator" && <Simulator
            players={players} leagues={metadata?.leagues || []} playerId={simulationId} setPlayerId={(id) => {
              setSimulationId(id);
              const p = players.find((item) => item.player_id === id);
              if (p) setSimInputs({ age: p.age, ovr: p.ovr, pot: p.pot, pace: p.pace, shooting: p.shooting, passing: p.passing, dribbling: p.dribbling, defending: p.defending, physical: p.physical, goals_p90: p.goals_p90, assists_p90: p.assists_p90, contract_years_left: p.contract_years_left, league: p.league });
              setSimulation(null);
            }}
            inputs={simInputs} setInputs={setSimInputs} result={simulation} busy={simBusy}
            onSimulate={async () => {
              if (!simulationId || !simInputs) return;
              setSimBusy(true);
              try { setSimulation(await api.simulate({ player_id: simulationId, ...simInputs })); }
              catch (err) { setError(err.message); }
              finally { setSimBusy(false); }
            }}
          />}
          {page === "diagnostics" && <ModelLab analytics={analytics} />}
        </div>
        <footer className="page-footer"><span>SCOUTIQ TALENT INTELLIGENCE</span><span>Player values are modelled estimates · {metadata?.player_count?.toLocaleString() || "—"} players indexed</span></footer>
      </main>
    </div>
  );
}

function PageHeading({ eyebrow, title, description, action }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="heading-action">{action}</div>}</div>;
}

function Overview({ players, metadata, analytics, busy, watchlist, onOpen, onNavigate, onWatch }) {
  const leaders = players.slice(0, 6);
  const avgValue = metadata?.average_value || 0;
  const opportunities = metadata?.value_gap_count || 0;
  const leagueValues = analytics?.league_values ? Object.entries(analytics.league_values) : [];
  return <>
    <PageHeading eyebrow="SCOUTING INTELLIGENCE · SEASON SNAPSHOT" title="Make the next move count." description="A clearer view of player quality, market signals, and the opportunities in between." action={<button className="button-primary" onClick={() => onNavigate("players")}><Compass size={16} /> Explore players <ArrowRight size={15} /></button>} />
    <div className="overview-hero">
      <div className="hero-copy"><div className="hero-kicker"><span /> SCOUTING BOARD <span className="hero-season">{metadata?.source || "PLAYER DATABASE"}</span></div><h2>Find the player<br /><em>before the market does.</em></h2><p>Browse a current season player snapshot, compare modelled value, and build a shortlist from more than {metadata?.player_count?.toLocaleString() || "—"} profiles.</p><button className="hero-link" onClick={() => onNavigate("value")}>Open value finder <ArrowRight size={15} /></button></div>
      <div className="hero-graphic" aria-hidden="true"><div className="field-ring ring-one" /><div className="field-ring ring-two" /><div className="field-center" /><div className="field-midline" /><div className="signal signal-a">VALUE GAP <b>+18%</b></div><div className="signal signal-b">PERFORMANCE <b>84.6</b></div><div className="signal signal-c"><span /> HIGH UPSIDE</div><div className="hero-ball">S</div></div>
      <div className="hero-aside"><span>SCOUTIQ INDEX</span><b>{analytics?.best_model || "MODEL"}</b><small>{metadata?.leagues?.length || 0} leagues · source data refreshed daily</small><div className="hero-aside-line" /><small>Use the database to filter by role, league, age, and value.</small></div>
    </div>
    <div className="kpi-grid">
      <MetricCard label="Players indexed" value={metadata?.player_count?.toLocaleString() || "—"} sub="across five top leagues" icon={Users} accent="green" />
      <MetricCard label="Average source value" value={money(avgValue)} sub="current player snapshot" icon={BarChart3} accent="blue" />
      <MetricCard label="Potential value gaps" value={opportunities.toLocaleString()} sub="players modelled above source" icon={TrendingUp} accent="amber" />
      <MetricCard label="Your shortlist" value={watchlist.length} sub="saved for follow-up" icon={Bookmark} accent="violet" onClick={() => onNavigate("players")} />
    </div>
    <section className="content-grid overview-grid">
      <div className="panel leader-panel"><div className="panel-heading"><div><span className="eyebrow">FORM WATCH</span><h2>Top performers</h2></div><button className="text-button" onClick={() => onNavigate("players")}>View database <ArrowRight size={14} /></button></div>
        <div className="leader-list">{busy && !leaders.length ? <LoadingRows /> : leaders.map((p, i) => <PlayerRow key={p.player_id} player={p} rank={i + 1} onOpen={onOpen} onWatch={onWatch} saved={watchlist.includes(p.player_id)} />)}</div>
      </div>
      <div className="panel league-panel"><div className="panel-heading"><div><span className="eyebrow">MARKET LANDSCAPE</span><h2>Median value by league</h2></div><BarChart3 size={17} /></div>
        {leagueValues.length ? <ResponsiveContainer width="100%" height={250}><BarChart data={leagueValues.map(([name, value]) => ({ name: titleCase(name), value }))} layout="vertical" margin={{ left: 4, right: 15, top: 6, bottom: 2 }}><CartesianGrid horizontal={false} stroke="#dce6f2" /><XAxis type="number" tickFormatter={(n) => `€${n}m`} tick={{ fill: "#728098", fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="name" width={105} tick={{ fill: "#43516a", fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip cursor={{ fill: "#edf4fc" }} contentStyle={{ background: "#ffffff", border: "1px solid #cbd9eb", borderRadius: 10, color: "#15243b" }} formatter={(value) => [money(value), "Median value"]} /><Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={12}>{leagueValues.map((entry, index) => <Cell key={entry[0]} fill={index === 0 ? "#2563eb" : "#75a9f5"} />)}</Bar></BarChart></ResponsiveContainer> : <div className="chart-skeleton"><LoaderCircle className="spin" size={20} /> Building league view</div>}
        <div className="source-note"><span className="note-dot" /> Values shown are the dataset's published estimates.</div>
      </div>
    </section>
  </>;
}

function MetricCard({ label, value, sub, icon: Icon, accent, onClick }) {
  return <div className={`metric-card accent-${accent} ${onClick ? "metric-clickable" : ""}`} onClick={onClick}><div className="metric-top"><span>{label}</span><Icon size={17} /></div><b>{value}</b><small>{sub}</small></div>;
}

function PlayerRow({ player, rank, onOpen, onWatch, saved }) {
  const delta = Number(player.val_delta_m || 0);
  return <div className="leader-row"><span className="rank-num">{String(rank).padStart(2, "0")}</span><div className="player-initial">{player.name?.split(/\s+/).map((part) => part[0]).slice(0, 2).join("")}</div><button className="row-player" onClick={() => onOpen(player.player_id)}><b>{player.name}</b><small>{player.club} <span>·</span> {player.position}</small></button><div className="row-rating"><small>RATING</small><b>{player.ovr}</b></div><div className="row-value"><small>VALUE GAP</small><b className={delta >= 0 ? "positive" : "negative"}>{delta >= 0 ? "+" : "−"}{shortMoney(Math.abs(delta))}</b></div><button className={`save-icon ${saved ? "saved" : ""}`} onClick={() => onWatch(player.player_id)} title={saved ? "Remove from shortlist" : "Save player"}>{saved ? <Star size={16} fill="currentColor" /> : <Bookmark size={16} />}</button><button className="row-open" onClick={() => onOpen(player.player_id)} aria-label={`Open ${player.name}`}><ArrowRight size={16} /></button></div>;
}

function PlayerDirectory({ players, total, busy, search, setSearch, league, setLeague, role, setRole, maxAge, setMaxAge, maxValue, setMaxValue, sort, setSort, leagues, roles, offset, setOffset, onOpen, watchlist, onWatch }) {
  const limit = 80;
  return <>
    <PageHeading eyebrow="SCOUTING WORKSPACE" title="Player database" description="Search, filter, and compare profiles across the available leagues." action={<div className="dataset-chip"><span className="note-dot" /> {total.toLocaleString()} PLAYERS</div>} />
    <div className="panel directory-panel">
      <div className="directory-toolbar"><div className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search player or club" /><kbd>⌘ K</kbd></div><div className="filter-control"><Filter size={15} /><span>Filters</span><ChevronDown size={14} /></div></div>
      <div className="filter-row"><Select value={league} onChange={setLeague} placeholder="All leagues" options={leagues.map((item) => [item, titleCase(item)])} /><Select value={role} onChange={setRole} placeholder="All positions" options={roles.map((item) => [item, titleCase(item)])} /><Select value={maxAge} onChange={setMaxAge} placeholder="All ages" options={[[23, "23 or younger"], [26, "26 or younger"], [30, "30 or younger"], [35, "35 or younger"], [45, "All ages"]]} /><Select value={maxValue} onChange={setMaxValue} placeholder="Any value" options={[[10, "Up to €10m"], [25, "Up to €25m"], [50, "Up to €50m"], [80, "Up to €80m"], [120, "Up to €120m"], [250, "Any value"]]} /><Select value={sort} onChange={setSort} placeholder="Sort" options={[["value", "Source value"], ["predicted", "Modelled value"], ["performance", "Performance score"], ["age", "Age"], ["name", "Name"]]} /><span className="result-count">Showing <b>{Math.min(offset + players.length, total)}</b> of {total.toLocaleString()}</span></div>
      <div className="table-wrap"><table className="player-table"><thead><tr><th>PLAYER</th><th>CLUB</th><th>LEAGUE</th><th>POS</th><th>AGE</th><th>OVR</th><th>SOURCE VAL</th><th>MODEL VAL</th><th>VALUE GAP</th><th /></tr></thead><tbody>
        {busy && !players.length ? <tr><td colSpan="10"><LoadingRows /></td></tr> : players.map((p) => <tr key={p.player_id} onDoubleClick={() => onOpen(p.player_id)}><td><button className="table-player" onClick={() => onOpen(p.player_id)}><span className="player-initial small-initial">{p.name?.split(/\s+/).map((part) => part[0]).slice(0, 2).join("")}</span><span><b>{p.name}</b></span></button></td><td>{p.club}</td><td>{p.league}</td><td><span className="position-pill">{p.position?.split(",")[0]}</span></td><td>{p.age}</td><td><span className="ovr-pill">{p.ovr}</span></td><td>{money(p.market_val_m)}</td><td>{money(p.pred_val_m)}</td><td><span className={`gap-pill ${p.val_delta_m >= 0 ? "positive-bg" : "negative-bg"}`}>{p.val_delta_m >= 0 ? "+" : "−"}{shortMoney(Math.abs(p.val_delta_m))}</span></td><td><button className={`save-icon ${watchlist.includes(p.player_id) ? "saved" : ""}`} onClick={() => onWatch(p.player_id)}>{watchlist.includes(p.player_id) ? <Star size={15} fill="currentColor" /> : <Bookmark size={15} />}</button></td></tr>)}
        {!busy && !players.length && <tr><td colSpan="10"><div className="empty-state"><Search size={21} /><b>No players match these filters</b><span>Try a broader search or clear a filter.</span></div></td></tr>}
      </tbody></table></div>
      <div className="pagination"><span>Showing {total ? offset + 1 : 0}–{Math.min(offset + limit, total)} of {total.toLocaleString()}</span><div><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}><ChevronLeft size={16} /> Previous</button><button disabled={offset + limit >= total} onClick={() => setOffset(offset + limit)}>Next <ChevronRight size={16} /></button></div></div>
    </div>
  </>;
}

function Select({ value, onChange, placeholder, options }) {
  return <label className="select-wrap"><select value={value} onChange={(event) => onChange(event.target.value)}><option value="">{placeholder}</option>{options.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select><ChevronDown size={14} /></label>;
}

function PlayerReport({ profile, loading, isSaved, onBack, onWatch, onCompare }) {
  if (loading) return <div className="loading-panel"><LoaderCircle className="spin" size={24} /><span>Loading player profile</span></div>;
  if (!profile) return null;
  const chartData = ["pace", "shooting", "passing", "dribbling", "defending", "physical"].map((key) => ({ attribute: titleCase(key), value: profile[key] || 0 }));
  const upside = Number(profile.pot || 0) - Number(profile.ovr || 0);
  return <>
    <button className="back-link" onClick={onBack}><ChevronLeft size={16} /> Player database</button>
    <div className="profile-hero panel"><div className="profile-orb">{profile.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("")}</div><div className="profile-identity"><div className="eyebrow">{profile.club} · {profile.league}</div><h1>{profile.name}</h1><div className="profile-meta"><span>{profile.position}</span><i /> <span>{profile.age} years</span></div></div><div className="profile-actions"><button className={`button-secondary ${isSaved ? "saved-button" : ""}`} onClick={onWatch}>{isSaved ? <Check size={15} /> : <Bookmark size={15} />}{isSaved ? "Shortlisted" : "Add to shortlist"}</button><button className="button-primary" onClick={onCompare}><Activity size={15} /> Compare</button></div></div>
    <div className="profile-kpis"><MetricCard label="Overall rating" value={profile.ovr} sub={`Potential ${profile.pot}`} icon={Gauge} accent="green" /><MetricCard label="Source value" value={money(profile.market_val_m)} sub="published estimate" icon={BarChart3} accent="blue" /><MetricCard label="Modelled value" value={money(profile.pred_val_m)} sub={`${profile.val_delta_m >= 0 ? "+" : "−"}${shortMoney(Math.abs(profile.val_delta_m))} vs source`} icon={TrendingUp} accent={profile.val_delta_m >= 0 ? "green" : "amber"} /><MetricCard label="Performance score" value={Number(profile.performance_score).toFixed(1)} sub="availability adjusted" icon={Activity} accent="violet" /></div>
    <div className="content-grid report-grid"><div className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow">PLAYER PROFILE</span><h2>Attribute map</h2></div><span className="profile-score"><b>{profile.ovr}</b><small>OVR</small></span></div><ResponsiveContainer width="100%" height={320}><RadarChart data={chartData} outerRadius="72%"><PolarGrid stroke="#d5e0ee" /><PolarAngleAxis dataKey="attribute" tick={{ fill: "#53637c", fontSize: 12 }} /><Radar dataKey="value" stroke="#2563eb" fill="#4f8df7" fillOpacity={0.2} strokeWidth={2} isAnimationActive /></RadarChart></ResponsiveContainer><div className="attribute-pills">{chartData.map((item) => <span key={item.attribute}>{item.attribute}<b>{item.value}</b></span>)}</div></div>
      <div className="panel report-insights"><div className="panel-heading"><div><span className="eyebrow">VALUE DRIVERS</span><h2>What moves the estimate</h2></div><Sparkles size={17} /></div><div className="upside-card"><span>DEVELOPMENT UPSIDE</span><b>+{upside}</b><small>rating points from current to potential</small><div className="upside-meter"><span style={{ width: `${Math.min(100, upside * 12)}%` }} /></div></div><div className="driver-list">{(profile.explanations || []).slice(0, 5).map((item) => <div className="driver-row" key={item.category}><span className="driver-mark"><span /></span><div><b>{item.category}</b><small>{item.description}</small></div><strong className={item.delta_eur_m >= 0 ? "positive" : "negative"}>{item.delta_eur_m >= 0 ? "+" : "−"}{shortMoney(Math.abs(item.delta_eur_m))}</strong></div>)}</div></div></div>
    <section className="panel match-panel"><div className="panel-heading"><div><span className="eyebrow">SEASON PRODUCTION</span><h2>Performance per 90</h2></div><div className="season-mini"><Clock3 size={14} /> Latest available season</div></div><div className="stat-strip"><Stat value={Number(profile.goals_p90 || 0).toFixed(2)} label="Goals / 90" hint={`xG ${Number(profile.xg_p90 || 0).toFixed(2)}`} /><Stat value={Number(profile.assists_p90 || 0).toFixed(2)} label="Assists / 90" hint={`xA ${Number(profile.xa_p90 || 0).toFixed(2)}`} /><Stat value={Number(profile.key_passes_p90 || 0).toFixed(1)} label="Key passes / 90" /><Stat value={Number(profile.tackles_won_p90 || 0).toFixed(1)} label="Tackles won / 90" /><Stat value={Number(profile.minutes || 0).toLocaleString()} label="Minutes" /><Stat value={Number(profile.contract_years_left || 0).toFixed(1)} label="Contract years" /></div></section>
  </>;
}

function Stat({ value, label, hint }) { return <div className="stat-cell"><b>{value}</b><span>{label}</span>{hint && <small>{hint}</small>}</div>; }

function ValueFinder({ budget, setBudget, under24, setUnder24, deals, count, loading, onOpen, onWatch, watchlist }) {
  return <>
    <PageHeading eyebrow="MARKET INTELLIGENCE" title="Value finder" description="Surface promising targets where the model sees more value than the source snapshot." action={<div className="dataset-chip"><TrendingUp size={14} /> {count} TARGETS</div>} />
    <div className="finder-toolbar panel"><div className="budget-control"><div><span className="eyebrow">MAX SOURCE VALUE</span><b>{money(budget, 0)}</b></div><input aria-label="Maximum player value" type="range" min="5" max="150" step="5" value={budget} onChange={(event) => setBudget(Number(event.target.value))} /></div><button className={`toggle-filter ${under24 ? "on" : ""}`} onClick={() => setUnder24(!under24)}><span className="toggle-track"><span /></span> Age 24 or younger</button><div className="finder-info"><Shield size={16} /><span>Ranked by model/source value ratio</span></div></div>
    <div className="deal-grid">{loading && !deals.length ? <LoadingRows /> : deals.map((p, index) => <DealCard key={p.player_id} player={p} index={index} onOpen={onOpen} onWatch={onWatch} saved={watchlist.includes(p.player_id)} />)}{!deals.length && !loading && <div className="panel empty-state"><Target size={22} /><b>No targets at this budget</b><span>Raise the maximum value or include all ages.</span></div>}</div>
  </>;
}

function DealCard({ player, index, onOpen, onWatch, saved }) {
  const gap = Number(player.val_delta_m || 0);
  return <article className="deal-card panel" style={{ "--card-order": index }}><div className="deal-card-top"><span className="deal-number">TARGET {String(index + 1).padStart(2, "0")}</span><button className={`save-icon ${saved ? "saved" : ""}`} onClick={() => onWatch(player.player_id)}>{saved ? <Star size={16} fill="currentColor" /> : <Bookmark size={16} />}</button></div><button className="deal-player" onClick={() => onOpen(player.player_id)}><span className="player-initial">{player.name?.split(/\s+/).map((part) => part[0]).slice(0, 2).join("")}</span><span><b>{player.name}</b><small>{player.club} · {player.age} yrs</small></span></button><div className="deal-gap"><div><span>SOURCE</span><b>{money(player.market_val_m)}</b></div><ArrowRight size={16} /><div><span>MODEL</span><b>{money(player.pred_val_m)}</b></div></div><div className="deal-card-bottom"><span className="positive"><ArrowUpRight size={15} /> {shortMoney(gap)} value gap</span><button className="text-button" onClick={() => onOpen(player.player_id)}>View profile <ArrowRight size={14} /></button></div></article>;
}

function ComparePage({ players, firstId, setFirstId, secondId, setSecondId, comparison, onOpen }) {
  const left = comparison[0];
  const right = comparison[1];
  const compareMetrics = [
    ["Modelled value", "pred_val_m", "money"], ["Source value", "market_val_m", "money"],
    ["Overall rating", "ovr"], ["Potential", "pot"], ["Performance score", "performance_score", "decimal"],
    ["Goals / 90", "goals_p90", "decimal"], ["Assists / 90", "assists_p90", "decimal"],
    ["Pace", "pace"], ["Shooting", "shooting"], ["Passing", "passing"],
    ["Dribbling", "dribbling"], ["Defending", "defending"], ["Physical", "physical"],
  ];
  const attributeData = left && right
    ? ["pace", "shooting", "passing", "dribbling", "defending", "physical"].map((key) => ({
      attribute: titleCase(key), playerA: Number(left[key] || 0), playerB: Number(right[key] || 0),
    }))
    : [];
  return <>
    <PageHeading eyebrow="PLAYER ANALYSIS" title="Compare players" description="Put two profiles side by side to see where each one leads." />
    <div className="compare-selectors"><CompareSelect label="PLAYER A" value={firstId} players={players} onChange={setFirstId} /><div className="versus">VS</div><CompareSelect label="PLAYER B" value={secondId} players={players} onChange={setSecondId} /></div>
    {left && right ? <div className="panel compare-panel">
      <div className="compare-heroes"><CompareHero player={left} tone="lime" onOpen={onOpen} /><div className="versus-badge">VS</div><CompareHero player={right} tone="blue" onOpen={onOpen} /></div>
      <section className="compare-attributes" aria-label="Player attribute comparison">
        <div className="compare-attributes-heading"><div><span className="eyebrow">PLAYER ATTRIBUTES</span><h2>Attribute comparison</h2></div><div className="compare-legend"><span><i className="compare-legend-a" />{left.name}</span><span><i className="compare-legend-b" />{right.name}</span></div></div>
        <div className="compare-radar-wrap"><ResponsiveContainer width="100%" height={310}><RadarChart data={attributeData} outerRadius="70%"><PolarGrid stroke="var(--chart-grid)" /><PolarAngleAxis dataKey="attribute" tick={{ fill: "var(--chart-label)", fontSize: 11 }} /><Tooltip formatter={(value, name) => [value, name]} labelFormatter={(label) => label} contentStyle={{ background: "var(--tooltip-bg)", border: "1px solid var(--tooltip-border)", borderRadius: 8, color: "var(--tooltip-text)", fontSize: 11 }} labelStyle={{ color: "var(--tooltip-text)" }} /><Radar dataKey="playerA" name={left.name} stroke="var(--chart-a)" fill="var(--chart-a)" fillOpacity={0.16} strokeWidth={2} activeDot={{ r: 5 }} isAnimationActive /><Radar dataKey="playerB" name={right.name} stroke="var(--chart-b)" fill="var(--chart-b)" fillOpacity={0.12} strokeWidth={2} activeDot={{ r: 5 }} isAnimationActive /></RadarChart></ResponsiveContainer></div>
      </section>
      <div className="compare-table">{compareMetrics.map(([label, key, type]) => <div className="compare-row" key={key}><span>{label}</span><b className={Number(left[key]) > Number(right[key]) ? "row-winner" : ""}>{type === "money" ? money(left[key]) : type === "decimal" ? Number(left[key] || 0).toFixed(1) : left[key]}</b><i><span style={{ width: `${Math.min(100, Math.max(5, Number(left[key]) / Math.max(Number(left[key]), Number(right[key]), 1) * 100))}%` }} /></i><i><span style={{ width: `${Math.min(100, Math.max(5, Number(right[key]) / Math.max(Number(left[key]), Number(right[key]), 1) * 100))}%` }} /></i><b className={Number(right[key]) > Number(left[key]) ? "row-winner" : ""}>{type === "money" ? money(right[key]) : type === "decimal" ? Number(right[key] || 0).toFixed(1) : right[key]}</b></div>)}</div>
    </div> : <div className="loading-panel"><LoaderCircle className="spin" size={22} /><span>Select two players to compare</span></div>}
  </>;
}

function CompareSelect({ label, value, players, onChange }) {
  return <label className="compare-select"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{players.map((player) => <option key={player.player_id} value={player.player_id}>{player.name} · {player.club}</option>)}</select><ChevronDown size={15} /></label>;
}
function CompareHero({ player, tone, onOpen }) { return <button className={`compare-hero ${tone}`} onClick={() => onOpen(player.player_id)}><span className="player-initial large-initial">{player.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("")}</span><span className="eyebrow">{player.club} · {player.position?.split(",")[0]}</span><b>{player.name}</b><small>{player.league}</small><span className="compare-hero-rating">{player.ovr}<small>OVR</small></span></button>; }

function Simulator({ players, leagues, playerId, setPlayerId, inputs, setInputs, result, busy, onSimulate }) {
  const selected = players.find((p) => p.player_id === playerId);
  const simulatorAttributes = ["pace", "shooting", "passing", "dribbling", "defending", "physical"].map((key) => ({
    attribute: titleCase(key), value: Number(inputs?.[key] ?? selected?.[key] ?? 0),
  }));
  const fields = [
    ["age", "Age", 16, 40], ["ovr", "Overall rating", 45, 99], ["pot", "Potential", 45, 99],
    ["pace", "Pace", 30, 99], ["shooting", "Shooting", 20, 99], ["passing", "Passing", 20, 99],
    ["dribbling", "Dribbling", 20, 99], ["defending", "Defending", 15, 99], ["physical", "Physical", 20, 99],
  ];
  return <>
    <PageHeading eyebrow="SCENARIO PLANNER" title="Value simulator" description="Adjust a player profile and see how the valuation model responds." />
    <div className="sim-layout"><div className="panel sim-controls"><div className="panel-heading"><div><span className="eyebrow">PLAYER BASELINE</span><h2>Build a scenario</h2></div><Settings2 size={17} /></div><div className="sim-player-select"><span>Starting player</span><CompareSelect value={playerId} players={players} onChange={setPlayerId} /></div>
      {inputs && <><div className="sim-field-grid">{fields.map(([key, label, min, max]) => <label className="range-field" key={key}><span>{label}<b>{inputs[key]}</b></span><input type="range" min={min} max={max} value={inputs[key] ?? min} onChange={(event) => setInputs({ ...inputs, [key]: Number(event.target.value) })} /></label>)}</div><div className="sim-performance-grid"><label>Goals / 90<input type="number" min="0" max="2" step="0.05" value={inputs.goals_p90 ?? 0} onChange={(event) => setInputs({ ...inputs, goals_p90: Number(event.target.value) })} /></label><label>Assists / 90<input type="number" min="0" max="2" step="0.05" value={inputs.assists_p90 ?? 0} onChange={(event) => setInputs({ ...inputs, assists_p90: Number(event.target.value) })} /></label><label>Contract years<input type="number" min="0" max="8" step="0.5" value={inputs.contract_years_left ?? 0} onChange={(event) => setInputs({ ...inputs, contract_years_left: Number(event.target.value) })} /></label><label>League<Select value={inputs.league} onChange={(value) => setInputs({ ...inputs, league: value })} placeholder="Other" options={leagues.map((item) => [item, titleCase(item)])} /></label></div><button className="button-primary run-sim" onClick={onSimulate} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />}{busy ? "Calculating scenario" : "Recalculate estimate"}<ArrowRight size={15} /></button></>}</div>
      <div className="sim-result"><div className="result-orbit"><span className="orbit-ring orbit-ring-one" /><span className="orbit-ring orbit-ring-two" /><Gauge size={18} /></div><span className="eyebrow">MODELLED PLAYER VALUE</span><h2>{result ? money(result.predicted_value) : selected ? money(selected.pred_val_m) : "—"}</h2><p>{result ? "Scenario estimate based on adjusted attributes" : "Run a scenario to calculate an updated estimate."}</p><div className="sim-radar-wrap" aria-label="Live player attribute profile"><ResponsiveContainer width="100%" height={210}><RadarChart data={simulatorAttributes} outerRadius="66%"><PolarGrid stroke="var(--chart-grid)" /><PolarAngleAxis dataKey="attribute" tick={{ fill: "var(--chart-label)", fontSize: 9 }} /><Radar dataKey="value" stroke="var(--chart-a)" fill="var(--chart-a)" fillOpacity={0.2} strokeWidth={2} isAnimationActive /></RadarChart></ResponsiveContainer></div><div className="result-range"><div><span>LOW RANGE</span><b>{money(result?.range_low ?? (selected?.pred_val_m * 0.9))}</b></div><div className="range-dash" /><div><span>HIGH RANGE</span><b>{money(result?.range_high ?? (selected?.pred_val_m * 1.1))}</b></div></div><div className="result-baseline"><span>Source value</span><b>{money(result?.baseline_value ?? selected?.market_val_m)}</b></div><div className="sim-note"><CircleHelp size={15} /><span>This is a directional estimate from ScoutIQ’s regression model, not a transfer fee quote.</span></div></div></div>
  </>;
}

function LoadingRows() { return <div className="loading-rows"><span /><span /><span /></div>; }

function ModelLab({ analytics }) {
  if (!analytics) return <div className="loading-panel"><LoaderCircle className="spin" size={22} /><span>Preparing model diagnostics</span></div>;
  const models = Object.entries(analytics.metrics || {});
  const modelChartData = models.map(([name, values]) => ({
    name: name.replace(" Regression", ""),
    fullName: name,
    r2: Number(values.R2_Score || 0),
    mae: Number(values.MAE_EUR_M || 0),
    rmse: Number(values.RMSE_EUR_M || 0),
    mape: Number(values.MAPE_Pct || 0),
  }));
  const featureData = (analytics.features || []).map((item) => ({
    name: item.display_name || item.feature,
    importance: Number(item.importance || 0) * 100,
  })).reverse();
  const chartTooltip = { background: "var(--tooltip-bg)", border: "1px solid var(--tooltip-border)", borderRadius: 8, color: "var(--tooltip-text)", fontSize: 10 };
  const axisTick = { fill: "var(--chart-label)", fontSize: 9 };
  return <>
    <PageHeading eyebrow="MODEL TRANSPARENCY" title="Model diagnostics" description="Review the candidate regressors and the signals that most influence their predictions." action={<div className="dataset-chip"><span className="note-dot" /> BEST FIT · {analytics.best_model}</div>} />
    <section className="model-grid">{models.map(([name, values]) => <article className={`panel model-card ${name === analytics.best_model ? "model-selected" : ""}`} key={name}><div className="model-card-top"><span className="eyebrow">{name === analytics.best_model ? "ACTIVE MODEL" : "CANDIDATE"}</span>{name === analytics.best_model && <span className="model-active"><Check size={12} /> BEST FIT</span>}</div><h2>{name.replace(" Regression", "")}</h2><div className="model-score"><b>{Number(values.R2_Score || 0).toFixed(3)}</b><span>R² score</span></div><div className="model-metrics"><span>Mean absolute error <b>{money(values.MAE_EUR_M)}</b></span><span>Root mean squared error <b>{money(values.RMSE_EUR_M)}</b></span><span>Mean percentage error <b>{Number(values.MAPE_Pct || 0).toFixed(1)}%</b></span></div></article>)}</section>
    <section className="diagnostics-chart-grid">
      <article className="panel diagnostics-chart-card"><div className="panel-heading"><div><span className="eyebrow">GOODNESS OF FIT</span><h2>R² score</h2></div><Activity size={17} /></div><p>Higher is better. Values closer to 1 explain more of the variation in player values.</p><ResponsiveContainer width="100%" height={230}><BarChart data={modelChartData} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}><CartesianGrid vertical={false} stroke="var(--chart-grid)" /><XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} /><YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={axisTick} axisLine={false} tickLine={false} /><Tooltip contentStyle={chartTooltip} labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullName || _label} formatter={(value) => [Number(value).toFixed(3), "R² score"]} /><Bar dataKey="r2" name="R² score" radius={[5, 5, 0, 0]}>{modelChartData.map((model) => <Cell key={model.fullName} fill={model.fullName === analytics.best_model ? "#2563eb" : "#8bb7f3"} />)}</Bar></BarChart></ResponsiveContainer></article>
      <article className="panel diagnostics-chart-card"><div className="panel-heading"><div><span className="eyebrow">ERROR IN VALUE UNITS</span><h2>MAE vs. RMSE</h2></div><BarChart3 size={17} /></div><p>Lower is better. MAE shows typical error; RMSE penalizes larger misses more.</p><ResponsiveContainer width="100%" height={230}><BarChart data={modelChartData} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}><CartesianGrid vertical={false} stroke="var(--chart-grid)" /><XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} /><YAxis tickFormatter={(value) => `€${Number(value).toFixed(0)}m`} tick={axisTick} axisLine={false} tickLine={false} /><Tooltip contentStyle={chartTooltip} labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullName || _label} formatter={(value, name) => [money(value), name]} /><Bar dataKey="mae" name="MAE" fill="#2563eb" radius={[4, 4, 0, 0]} /><Bar dataKey="rmse" name="RMSE" fill="#8bb7f3" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer><div className="diagnostics-legend"><span><i className="legend-blue" />MAE</span><span><i className="legend-light-blue" />RMSE</span></div></article>
      <article className="panel diagnostics-chart-card"><div className="panel-heading"><div><span className="eyebrow">RELATIVE ERROR</span><h2>MAPE</h2></div><TrendingUp size={17} /></div><p>Average absolute error as a percentage of the actual player value. Lower is better.</p><ResponsiveContainer width="100%" height={230}><BarChart data={modelChartData} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}><CartesianGrid vertical={false} stroke="var(--chart-grid)" /><XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} /><YAxis tickFormatter={(value) => `${Number(value).toFixed(0)}%`} tick={axisTick} axisLine={false} tickLine={false} /><Tooltip contentStyle={chartTooltip} labelFormatter={(_label, payload) => payload?.[0]?.payload?.fullName || _label} formatter={(value) => [`${Number(value).toFixed(2)}%`, "MAPE"]} /><Bar dataKey="mape" name="MAPE" fill="#4f83df" radius={[5, 5, 0, 0]}>{modelChartData.map((model) => <Cell key={model.fullName} fill={model.fullName === analytics.best_model ? "#2563eb" : "#8bb7f3"} />)}</Bar></BarChart></ResponsiveContainer></article>
    </section>
    <section className="panel feature-panel"><div className="panel-heading"><div><span className="eyebrow">MODEL INTERPRETABILITY</span><h2>Top valuation signals</h2></div><Sparkles size={17} /></div><p className="feature-caption">Relative importance from the gradient boosting model. Higher bars indicate more influence across the training set.</p><ResponsiveContainer width="100%" height={320}><BarChart data={featureData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}><CartesianGrid horizontal={false} stroke="#dce6f2" /><XAxis type="number" tickFormatter={(value) => `${value.toFixed(0)}%`} tick={{ fill: "#728098", fontSize: 9 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="name" width={175} tick={{ fill: "#43516a", fontSize: 9 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #cbd9eb", borderRadius: 8, color: "#15243b", fontSize: 10 }} formatter={(value) => [`${Number(value).toFixed(2)}%`, "Importance"]} /><Bar dataKey="importance" fill="#2563eb" radius={[0, 5, 5, 0]} barSize={14} isAnimationActive /></BarChart></ResponsiveContainer><div className="model-footnote"><CircleHelp size={14} /><span>Model scores describe a held-out sample from this dataset. They do not guarantee future valuation accuracy.</span></div></section>
  </>;
}

export default App;

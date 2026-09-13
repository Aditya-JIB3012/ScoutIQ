"""Custom high-end sports tech design system and CSS styling for ScoutIQ."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* Global Reset & Futuristic Stadium Atmosphere */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: radial-gradient(circle at 50% -10%, rgba(16, 185, 129, 0.12) 0%, rgba(14, 165, 233, 0.06) 35%, #050811 75%);
    background-color: #050811;
    color: #e2e8f0;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #090d1a;
}
::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #10b981;
}

/* Broadcast Header Banner */
.scoutiq-header {
    position: relative;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(11, 20, 38, 0.85) 60%, rgba(6, 78, 59, 0.4) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 1.8rem 2.2rem;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    margin-bottom: 2rem;
    overflow: hidden;
}

.scoutiq-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #10b981, #38bdf8, #f59e0b, #10b981);
    background-size: 200% auto;
    animation: gradientShift 6s linear infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}

.scoutiq-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 30%, #38bdf8 70%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.scoutiq-subtitle {
    font-size: 0.95rem;
    color: #94a3b8;
    margin-top: 0.4rem;
    font-weight: 400;
}

/* Pulsing Live Dot */
.live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #10b981;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
}

.pulse-dot {
    width: 7px;
    height: 7px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 0 rgba(16, 185, 129, 0.7);
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Glassmorphic Metric Card */
.stat-card-pro {
    background: linear-gradient(145deg, rgba(17, 26, 46, 0.75) 0%, rgba(10, 16, 30, 0.85) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.stat-card-pro:hover {
    transform: translateY(-3px);
    border-color: rgba(16, 185, 129, 0.35);
    box-shadow: 0 16px 35px -8px rgba(16, 185, 129, 0.15);
}

.stat-card-pro::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 50px;
    height: 50px;
    background: radial-gradient(circle at top right, rgba(16, 185, 129, 0.1), transparent 70%);
}

.stat-label-pro {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
}

.stat-value-pro {
    font-size: 1.85rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.02em;
    font-feature-settings: "tnum";
}

.stat-meta-pro {
    font-size: 0.8rem;
    margin-top: 0.3rem;
    font-weight: 500;
}

/* Tactical Position Badges */
.badge-role-att {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

.badge-role-wng {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

.badge-role-mid {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

.badge-role-def {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

.badge-role-gk {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.3);
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
}

/* OVR Shield Badge */
.ovr-shield {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: #0f172a;
    font-weight: 900;
    font-size: 1.25rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(245, 158, 11, 0.35);
}

.pot-shield {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    font-weight: 800;
    font-size: 0.95rem;
    border-radius: 10px;
}

/* Player Showcase Hero Card */
.player-hero-card {
    background: linear-gradient(135deg, rgba(17, 26, 48, 0.85) 0%, rgba(13, 20, 36, 0.95) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 1.8rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
}

/* Moneyball Deal Card */
.deal-card {
    background: linear-gradient(145deg, rgba(13, 33, 35, 0.75) 0%, rgba(9, 21, 28, 0.85) 100%);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 16px;
    padding: 1.3rem;
    margin-bottom: 1.2rem;
    transition: all 0.2s ease;
    box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.4);
}

.deal-card:hover {
    transform: translateY(-2px);
    border-color: #10b981;
    box-shadow: 0 15px 30px -8px rgba(16, 185, 129, 0.25);
}

/* Streamlit Tabs Overhaul */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(11, 17, 32, 0.7);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
    color: #94a3b8;
    background-color: transparent;
    transition: all 0.2s ease;
    border: none !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #f8fafc;
    background-color: rgba(255, 255, 255, 0.04);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(14, 165, 233, 0.15) 100%) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16, 185, 129, 0.4) !important;
    box-shadow: 0 4px 15px -3px rgba(16, 185, 129, 0.25);
}

/* Streamlit Selectbox and Sliders Modernization */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
}

/* Custom Table Polish */
.stDataFrame {
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    overflow: hidden;
}

/* Container Spacing */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3.5rem;
    max-width: 1350px;
}
</style>
"""

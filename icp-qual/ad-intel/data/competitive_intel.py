"""Competitive Intelligence Reference Data

CTV competitor positioning, creative models, sell motions, and discovery
questions. Used by the pipeline to generate competitive context in reports
and Slack messages when a brand is detected using a competitor platform.

Source: Upscale competitive landscape docs (April 2026)
"""

# ---------------------------------------------------------------------------
# Market stats — for use in reports and pitch sections
# ---------------------------------------------------------------------------

MARKET_STATS = {
    "streaming_share": "44.8%",
    "streaming_share_source": "Nielsen, June 2025",
    "youtube_primary_device": "TV screen — more than desktop and mobile combined",
    "us_streaming_households": "99% of U.S. households use at least one streaming service",
    "time_streaming_vs_social": "1.4x more time on streaming than social media",
    "roku_households": "90M+ streaming households (~50% of U.S. broadband HHs)",
    "tubi_mau": "97M+ MAUs, 10B+ hours streamed in 2024",
    "ctv_ad_spend_growth": "16% YoY in 2024, projected $32.57B in 2025",
}

# ---------------------------------------------------------------------------
# Creative Reality Matrix — the #1 competitive differentiator
# ---------------------------------------------------------------------------

CREATIVE_REALITY_MATRIX = {
    "Vibe": {
        "tool": "Vibe Studio",
        "verdict": "AI template generator",
        "response": (
            "Vibe Studio is a self-serve template tool. It doesn't read your brand guide, "
            "doesn't know your SKUs, and doesn't produce 4-12 net new ads/month from your "
            "real product assets."
        ),
    },
    "MNTN": {
        "tool": "QuickFrame AI",
        "verdict": "Outsourced vendor (AI/template)",
        "response": (
            "MNTN doesn't make your ads — they send you to a third-party tool. "
            "AI/template output, not brand-specific production. You're handed off after signing."
        ),
    },
    "tvScientific": {
        "tool": "Creative Advisor",
        "verdict": "Scoring tool only — zero production",
        "response": (
            "Tells you what's working. Doesn't make more of it. No production capacity. "
            "Great measurement with no creative engine is an expensive way to watch the same "
            "ads slowly fade."
        ),
    },
    "Tatari": {
        "tool": "Creative Library",
        "verdict": "Upload/manage — not produce",
        "response": (
            "Tatari does not make ads. If you need creative, they point you to agencies. "
            "Assumes creative is solved — which it isn't for most ecommerce brands."
        ),
    },
    "Universal Ads": {
        "tool": "AI Video Generator",
        "verdict": "Generic AI slop — fails brand guides",
        "response": (
            "Doesn't know your brand, SKUs, or visual identity. Outputs stock footage + "
            "text overlays that look nothing like your actual brand creative."
        ),
    },
    "Upscale": {
        "tool": "In-house Creative Team",
        "verdict": "4-12 net new brand-matched ads/month",
        "response": (
            "Brief-based, brand-matched, performance-tested. Built from your actual product "
            "assets and brand guide. No outsourcing, no templates, no AI slop."
        ),
    },
}

# ---------------------------------------------------------------------------
# Competitor platform profiles
# ---------------------------------------------------------------------------

COMPETITORS = {
    "Tatari": {
        "positioning": "Convergent TV infrastructure with deep measurement but no creative production",
        "creative_model": "Creative Library — upload/manage only, does not produce ads",
        "creative_verdict": "Assumes creative is solved. Points brands to agencies.",
        "buyer_profile": "DTC brands with existing in-house creative, sophisticated growth marketers",
        "measurement": "Strongest multi-method: Tatari View-through, Digital View-through, Incremental, MMM, MTA, DOE",
        "g2_score": "0 reviews",
        "case_studies": "30+ named — deepest DTC library (Made In, Fabletics, Seed, Knix, Vuori, Jones Road Beauty, BYLT)",
        "best_short_pitch": (
            "Tatari is strong convergent-TV infrastructure with excellent measurement depth. "
            "But Creative Library is an asset management tool — Tatari doesn't make ads. "
            "Upscale wins when the buyer wants an ecommerce creative engine bundled into the "
            "operating model, not a TV platform that assumes creative is already solved."
        ),
        "where_upscale_presses": (
            "Tatari assumes creative is solved. Upscale makes it. For lean ecommerce teams "
            "that don't want to build TV-specific internal muscle, Upscale's bundled creative + "
            "media + measurement model wins. Tatari is for TV operators; Upscale is for ecommerce "
            "brands that want TV to perform."
        ),
        "sell_motions": [
            "Tatari manages your creative — Upscale makes it. 'Creative Library — who produces the ads that go into it?'",
            "Ecommerce execution engine vs TV-operator platform — Upscale is built for lean ecommerce teams",
            "Streaming TV + YouTube without linear complexity",
        ],
        "discovery_questions": [
            "Creative Library — who actually produces the ads that go into it?",
            "Do you have a reliable pipeline of TV-ready creative, or is that the bottleneck?",
            "How many net new CTV creatives did you produce last quarter?",
            "Do you actually need linear TV this year, or is proving profitable streaming + video growth the priority?",
        ],
        "landmines": [
            "Don't say Tatari lacks self-serve — it offers all three service models",
            "Don't say Tatari is opaque on pricing — they emphasize transparent pricing",
            "Never say 'lacks creative' — frame as 'asset management tool vs in-house production team'",
        ],
        "objections": [
            {"objection": "Tatari has stronger measurement and incrementality.",
             "response": "Agreed — Tatari's measurement depth is excellent. But great measurement needs creative volume to work with. Upscale makes 4-12 net new brand-matched ads per month — that's the fuel that makes measurement meaningful."},
            {"objection": "Tatari does linear, CTV, and OLV — more complete.",
             "response": "More complete if the buyer needs convergent TV now. But for a lean ecommerce team, more surface area means more complexity. Upscale is narrower by design: Streaming TV + YouTube, in-house creative production, commerce-native measurement."},
            {"objection": "Tatari can start small too.",
             "response": "True. But starting small isn't the question. The question is: who makes the ads? Tatari assumes you have creative. Upscale makes it — 4-12 net new brand-matched ads per month, continuously."},
        ],
        "attribution": {
            "native_tracking": "Tatari View-through, Digital View-through, and Incremental attribution via proprietary device graph + shared-IP filtering",
            "core_logic": "TV-specific device graph for Tatari View-through (conservative TV-native); Digital View-through uses IP-matching aligned with digital platforms",
            "windows": "CPV/CPI/CAC/ROAS, DragFactor for immediate vs delayed response, dashboard cuts by network/creative/DMA/platform, S3 exports",
            "extensions": "MMM, MTA, design of experiments, post-purchase surveys. Explicit triangulation philosophy — no single source of truth.",
            "bottom_line": "Broadest public measurement taxonomy and clearest philosophy that no single attribution method is enough on its own.",
        },
    },
    "MNTN": {
        "positioning": "Premium Performance TV platform with outsourced creative via QuickFrame",
        "creative_model": "QuickFrame AI — outsourced vendor (AI/template), not MNTN's in-house team",
        "creative_verdict": "Doesn't make your ads — sends you to a third-party tool.",
        "buyer_profile": "Mid-market and enterprise brands, agencies, B2B advertisers",
        "measurement": "Verified Visits via household graph, Last Touch dedupes, Haus incrementality",
        "g2_score": "4.9/5 (56 reviews)",
        "case_studies": "100+ (Onewheel 15x ROAS, Dagne Dover 9.9x ROAS, Kane Footwear 250% higher ROAS)",
        "best_short_pitch": (
            "MNTN is strong Performance TV infrastructure. Upscale wins when the buyer wants "
            "a real creative partner making 4-12 brand-matched ads per month — not a third-party "
            "vendor handoff — and a cleaner Streaming TV + YouTube operating model."
        ),
        "where_upscale_presses": (
            "Ecommerce specialization, YouTube + Streaming TV under one operating model, "
            "in-house creative vs outsourced QuickFrame vendor, and simpler bundled deliverables "
            "vs opaque margin-based buying."
        ),
        "sell_motions": [
            "Upscale makes your ads — QuickFrame is a vendor MNTN sends you to",
            "Bundled deliverables vs margin-based buying + outsourced creative",
            "One operating layer for Streaming TV + YouTube — not just premium CTV inventory",
        ],
        "discovery_questions": [
            "When MNTN says creative is included — who actually makes the ad? Their team or QuickFrame?",
            "How many net new brand-matched creatives did QuickFrame produce for your brand last quarter?",
            "Are you solving for premium CTV only, or a broader big-screen program including YouTube?",
            "Does your procurement team care about clearly packaged deliverables vs margin-inside-media?",
        ],
        "landmines": [
            "Don't say MNTN 'hides fees' — accurate: retains undisclosed margin within media spend",
            "Don't say MNTN can't touch YouTube — QuickFrame can export there",
            "Don't say MNTN lacks incrementality — has public pages and Haus",
        ],
        "objections": [
            {"objection": "MNTN has QuickFrame too.",
             "response": "QuickFrame is an outsourced vendor, not MNTN's in-house creative team. AI/template output — not brand-matched, not brief-based, not continuously delivering 4-12 net new performance ads per month."},
            {"objection": "MNTN has better inventory.",
             "response": "Agreed — 150+ premium networks is strong. But premium inventory with weak, template-based creative underperforms. The creative is what drives outcomes. Upscale makes 4-12 real, brand-matched ads per month."},
            {"objection": "MNTN is proven and easy.",
             "response": "Agree on brand maturity and UX. The question isn't ease of use — it's who makes your ads. QuickFrame is a vendor you're handed off to. Upscale is an in-house creative partner that makes the ads month over month."},
        ],
        "attribution": {
            "native_tracking": "MNTN pixel + Multi-Touch ad clicks; viewability required for Verified Visit credit",
            "core_logic": "Verified Visits via proprietary household graph spanning 132M households; Last Touch variant dedupes by referring params (email, paid-search UTMs)",
            "windows": "7-day retargeting, 14-day prospecting defaults",
            "extensions": "GA, Rockerbox, Northbeam, Haus GeoLift, CallRail, Freshpaint, Comprehensive Reporting (modeled outcomes)",
            "bottom_line": "Clearest out-of-the-box performance attribution product story: productized household-graph model with explicit rules, windows, and deduping.",
        },
    },
    "tvScientific": {
        "positioning": "Measurement-first Performance TV with patented attribution",
        "creative_model": "Creative Advisor — scoring tool only, zero ad production",
        "creative_verdict": "Tells you what's working. Doesn't make more of it.",
        "buyer_profile": "Advanced performance marketers, app-install and affiliate-heavy use cases",
        "measurement": "Strongest public: patented household-signal attribution + incremental lift, log-level transparency",
        "g2_score": "0 reviews",
        "case_studies": "~15 named (Dell 50x ROAS, LG 1,100% revenue growth, Wildgrain 150% YoY)",
        "best_short_pitch": (
            "tvScientific is the measurement-first option and their measurement story is genuinely "
            "excellent. But Creative Advisor is a scoring tool — not a production team. Upscale wins "
            "when the brand's real bottleneck is creative volume and velocity."
        ),
        "where_upscale_presses": (
            "Win on creative generation, not measurement contest. The gap between 2x and 6x ROAS "
            "is usually more and better creative variants, not more sophisticated attribution. "
            "Upscale makes 4-12 net new brand-matched ads/month — then we measure what wins."
        ),
        "sell_motions": [
            "You can't measure your way out of bad or missing creative",
            "Creative velocity is the performance lever that measurement can't replace",
            "Commerce-native creative system vs multi-vertical measurement platform",
        ],
        "discovery_questions": [
            "Creative Advisor scores your creative — but who makes the new ads when a variant underperforms?",
            "How many net new CTV-ready creatives did your brand produce last quarter?",
            "Is your hardest problem attribution confidence, or producing enough good creative to make TV scale?",
        ],
        "landmines": [
            "Don't say tvScientific lacks transparency, log-level data, or incrementality — their strongest claims",
            "Never say 'has no creative' — frame as 'scoring tool vs in-house production team'",
        ],
        "objections": [
            {"objection": "tvScientific has stronger attribution.",
             "response": "Agreed — strongest public measurement story. Don't fight it. Great measurement needs great creative to measure. If the brand can't produce 4-12 net new ads per month, the most sophisticated attribution doesn't help."},
            {"objection": "They guarantee outcomes.",
             "response": "Meaningful for qualified advertisers. But guaranteed buying doesn't solve the creative-volume problem. Running the same 2 ads on a guaranteed CPO model will plateau. Creative velocity is what unlocks compounding results."},
            {"objection": "Creative Advisor tells us what's working.",
             "response": "Scoring existing creative is step 1. Step 2 is making more of what's working and iterating on what isn't. tvScientific doesn't do step 2. Upscale does: 4-12 net new brand-matched ads per month."},
        ],
        "attribution": {
            "native_tracking": "Household exposure/timing/response criteria with partner integrations; transparent analytics and on-demand reporting",
            "core_logic": "Patented household-signal attribution linking ad exposure to conversions at household level; unified deterministic + incremental lift framework",
            "windows": "Defined attribution window; full-path analytics including cases where CTV is not final touch; online + offline conversion data",
            "extensions": "Airbridge, Invoca, Measured, Rockerbox, Triple Whale, Adjust, AppsFlyer",
            "bottom_line": "Strongest public emphasis on deterministic + incremental measurement as one operating system, not just a partner add-on.",
        },
    },
    "Vibe": {
        "positioning": "Self-serve CTV on-ramp with Vibe Studio template builder",
        "creative_model": "Vibe Studio — AI template generator, doesn't read brand guides",
        "creative_verdict": "Template generator. Brand quality depends entirely on you.",
        "buyer_profile": "SMBs, agencies, brands testing CTV for first time, $50/day minimum",
        "measurement": "IP/pixel-first, partner-led incrementality (Haus, INCRMNTAL)",
        "g2_score": "4.8/5 (132 reviews)",
        "case_studies": "44 total (Cycling Frog 678% ROAS, Blindster 14x ROAS, IMVU 60% more purchases)",
        "best_short_pitch": (
            "Vibe is a credible self-serve starting point. Upscale wins when an ecommerce brand "
            "needs TV to become a repeatable growth channel with 4-12 real brand-matched ads "
            "per month — not templates you fill in yourself."
        ),
        "where_upscale_presses": (
            "Reframe from low-friction test tool to repeatable ecommerce growth engine. "
            "Vibe is a credible 'start' platform. Upscale is the better 'scale' platform — "
            "creative system depth, 4-12 net new brand-matched ads/month, bundled workflow, "
            "and a broader Streaming TV + YouTube operating model."
        ),
        "sell_motions": [
            "We make the ads — Vibe makes you figure it out",
            "Creative velocity compounds — 4-12 net new ads/month vs one-time templates",
            "Broader big-screen operating model: Streaming TV + YouTube unified",
        ],
        "discovery_questions": [
            "What does your current CTV creative pipeline look like — how many net new ads last quarter?",
            "Has your team seen the output from Vibe Studio? How does it compare to your paid social quality?",
            "Who owns creative production today — internal team, agency, or the CTV platform?",
        ],
        "landmines": [
            "Don't say Vibe lacks transparency post-Certified Supply launch (Nov 2025)",
            "Don't say Vibe cannot scale — they push back publicly",
            "Don't say Vibe lacks incrementality — Haus partnership is live",
        ],
        "objections": [
            {"objection": "Vibe Studio handles creative.",
             "response": "Vibe Studio is a template generator — it doesn't make brand-matched, performance-tested ads. Upscale's in-house team delivers 4-12 net new ads per month, briefed on your brand, built from your actual assets."},
            {"objection": "Vibe is cheaper and faster to launch.",
             "response": "Agree for a first test. But once TV is expected to scale, the bottleneck becomes creative velocity and quality. Template-based creative hits a ceiling. 4-12 net new brand-matched ads per month is what makes TV a repeatable growth channel."},
            {"objection": "We already have internal creative.",
             "response": "Then pivot to measurement, first-party commerce optimization, and the Streaming TV + YouTube operating model. But ask: is your team producing 4-12 net new CTV-optimized ads per month?"},
        ],
        "attribution": {
            "native_tracking": "Vibe Pixel for page views, leads, purchases; IP-address matching for web; app attribution via MMP",
            "core_logic": "Logs household IP when Smart TV ad plays, matches later site activity from same Wi-Fi network within attribution window",
            "windows": "Configurable: 12h, 1d, 48h, 72h, 7d, 30d (docs not fully harmonized on exact options)",
            "extensions": "GA, CallRail, Haus, INCRMNTAL, Lifesight, Northbeam, Prescient, Triple Whale, WorkMagic; app MMPs (Adjust, AppsFlyer, Kochava, Singular)",
            "bottom_line": "Cleanest pixel/IP-first story. Easy to understand and operationally simple, but advanced incrementality and cross-channel attribution is partner-led.",
        },
    },
    "Universal Ads": {
        "positioning": "Premium publisher-direct TV access via Comcast/NBCU with AI video generation",
        "creative_model": "AI Video Generator — generic AI, doesn't know brand/SKUs/visual identity",
        "creative_verdict": "Outputs stock footage + text overlays that fail brand guidelines.",
        "buyer_profile": "SMBs, performance marketers diversifying beyond Meta/Google",
        "measurement": "UA Pixel, 7/14/30-day lookbacks, partner-led advanced measurement",
        "g2_score": "N/A",
        "case_studies": "3 confirmed (Jones Road Beauty, Palmer's, QB1 Jerky)",
        "best_short_pitch": (
            "Universal Ads is a compelling premium-TV on-ramp with unique NBCU inventory. "
            "But their AI Video Generator doesn't know your brand — it fails brand guidelines. "
            "Upscale wins when a brand needs more than TV access: an in-house creative team."
        ),
        "where_upscale_presses": (
            "Move from access to outcomes. Universal Ads is a compelling TV on-ramp. Upscale "
            "is the better system when a brand needs more than access: in-house creative production, "
            "4-12 brand-matched ads/month, and measurement that extends beyond the publisher relationship."
        ),
        "sell_motions": [
            "AI slop vs brand-matched creative — who makes the real ads?",
            "Continuous creative production vs one-and-done AI generation",
            "Ecommerce growth system vs low-friction premium TV on-ramp",
        ],
        "discovery_questions": [
            "What does the AI Video Generator actually output — have you seen it run against your brand guide?",
            "Who owns creative production after you open the account?",
            "Is premium publisher access the top priority, or do you need a creative partner?",
        ],
        "landmines": [
            "Don't say 'lacks creative' — frame as 'generic AI slop vs in-house brand-matched production'",
            "Don't say Universal Ads lacks targeting — it has pixel, custom audiences",
            "Don't claim no markups as fact — community chatter, not verified",
        ],
        "objections": [
            {"objection": "They have AI creative built in.",
             "response": "AI creative that doesn't know your brand, your SKUs, or your visual identity isn't creative — it's a placeholder. Upscale's in-house team makes 4-12 net new brand-matched performance ads per month."},
            {"objection": "Universal Ads is simpler and has no contracts.",
             "response": "Agree — no-contract self-serve with premium inventory is compelling. But simple access doesn't mean strong performance creative. Upscale bundles in-house creative production into the operating model."},
            {"objection": "They have access to premium publishers we want.",
             "response": "Valid — especially for NBCU/Olympic inventory. Don't fight unique inventory. Position Upscale as the better ongoing system: in-house creative production, 4-12 ads/month, and measurement that extends beyond the publisher relationship."},
        ],
        "attribution": {
            "native_tracking": "UA Pixel single JavaScript tag in global header; tracks up to 18 events including custom events",
            "core_logic": "Pixel-based web attribution with 7/14/30-day lookback windows; custom audiences for targeting or exclusion",
            "windows": "7-day, 14-day, 30-day lookbacks (switchable in reporting)",
            "extensions": "Measurement partners for incrementality and advanced attribution; Marketing API for scale",
            "bottom_line": "Simplest self-serve measurement stack: one pixel, standard lookbacks, partner-led advanced measurement, and API access.",
        },
    },
}

# ---------------------------------------------------------------------------
# Master Competitive Matrix — feature comparison across platforms
# ✓ = Yes/Strong, ~ = Partial/Limited, ✗ = No/Not offered
# ---------------------------------------------------------------------------

COMPETITIVE_MATRIX = {
    "features": [
        "In-house creative team",
        "4-12 net new ads/month",
        "Brand-matched (reads brand guide)",
        "Built from actual product assets",
        "eCommerce / DTC specialization",
        "Streaming TV buying + measurement",
        "YouTube in same operating model",
        "Built-in attribution + incrementality",
        "Shopify / 1P data integration",
        "Bundled pricing (creative + media + measurement)",
        "No minimum spend",
        "Self-serve option",
        "Linear TV (broadcast)",
    ],
    "platforms": {
        "Upscale": ["✓", "✓", "✓", "✓", "✓", "✓", "✓", "✓", "✓", "✓", "~", "~", "✗"],
        "Vibe": ["✗", "✗", "✗", "✗", "~", "✓", "~", "~", "✓", "~", "✓", "✓", "✗"],
        "MNTN": ["✗", "✗", "✗", "~", "~", "✓", "~", "✓", "~", "✗", "~", "✓", "✗"],
        "tvScientific": ["✗", "✗", "✗", "~", "✗", "✓", "✗", "✓", "~", "✗", "✓", "✓", "✗"],
        "Tatari": ["✗", "✗", "✗", "~", "~", "✓", "~", "✓", "~", "✗", "~", "✓", "✓"],
        "Universal Ads": ["✗", "✗", "✗", "✗", "✗", "✓", "✗", "~", "~", "~", "✓", "✓", "✗"],
    },
}

# ---------------------------------------------------------------------------
# Brands known to appear in competitor case studies
# Includes vertical and prospect context for warm outbound intelligence
# ---------------------------------------------------------------------------

COMPETITOR_CASE_STUDY_BRANDS: dict[str, dict] = {
    # --- Tatari DTC (highest ICP overlap) ---
    "madein.com": {
        "competitors": ["Tatari"],
        "vertical": "DTC / Cookware",
        "why_prospect": "TV became their largest acquisition channel. Now at scale — creative velocity is likely the next bottleneck.",
    },
    "fabletics.com": {
        "competitors": ["Tatari"],
        "vertical": "Fashion / Subscription",
        "why_prospect": "Real-time data and creative tests driving measurable traffic. High creative volume need across SKU launches.",
    },
    "seed.com": {
        "competitors": ["Tatari"],
        "vertical": "Health / Probiotics",
        "why_prospect": "Doubled conversions during peak seasons. Promo-calendar brand with high creative refresh needs.",
    },
    "knix.com": {
        "competitors": ["Tatari"],
        "vertical": "DTC / Intimates",
        "why_prospect": "Lowered acquisition costs, uncovered new audiences. Continuous optimization brand.",
    },
    "vuori.com": {
        "competitors": ["Tatari"],
        "vertical": "DTC / Activewear",
        "why_prospect": "$150K test turned into always-on channel. Proved TV works — now needs to scale creative to match.",
    },
    "aroma360.com": {
        "competitors": ["Tatari"],
        "vertical": "Luxury / Fragrance",
        "why_prospect": "80% CPA reduction, doubled ROAS. High-performing brand ready to press creative advantage.",
    },
    "byltbasics.com": {
        "competitors": ["Tatari"],
        "vertical": "DTC / Apparel",
        "why_prospect": "Full-funnel TV + holiday revenue. Multi-SKU brand with strong seasonal creative needs.",
    },
    "jonesroadbeauty.com": {
        "competitors": ["Tatari", "Universal Ads"],
        "vertical": "Beauty / DTC",
        "why_prospect": "On both Tatari AND Universal Ads case studies. Clearly active CTV spender with major creative program.",
    },
    "tecovas.com": {
        "competitors": ["Tatari"],
        "vertical": "DTC / Boots",
        "why_prospect": "World Series spot drove 16x visit increase. High-moment brand with seasonal creative needs.",
    },
    "calm.com": {
        "competitors": ["Tatari"],
        "vertical": "Health / Wellness App",
        "why_prospect": "LeBron James partnership, AdAge Marketer of the Year. Premium creative brand.",
    },
    "fiverr.com": {
        "competitors": ["Tatari"],
        "vertical": "Marketplace",
        "why_prospect": "75% CAC reduction with post-Super Bowl retargeting. Performance-driven TV buyer.",
    },
    # --- MNTN ---
    "dagnedover.com": {
        "competitors": ["MNTN"],
        "vertical": "DTC / Accessories",
        "why_prospect": "9.9x ROAS via retargeting. Creative-quality brand that would benefit from brand-matched production.",
    },
    "kanefootwear.com": {
        "competitors": ["MNTN"],
        "vertical": "Footwear",
        "why_prospect": "250% higher ROAS than goal. Science-backed brand with education-heavy creative needs.",
    },
    "onewheel.com": {
        "competitors": ["MNTN"],
        "vertical": "DTC / Electric Vehicles",
        "why_prospect": "15x ROAS, 95% lower CPA. High-performance brand proven on CTV.",
    },
    "talkspace.com": {
        "competitors": ["MNTN"],
        "vertical": "Health / Telehealth",
        "why_prospect": "67% lower CPA on CTV. Subscription brand with ongoing creative needs.",
    },
    "jlindeberg.com": {
        "competitors": ["MNTN"],
        "vertical": "Fashion / Golf",
        "why_prospect": "9x ROAS. Premium fashion brand with seasonal creative needs.",
    },
    "nationalbusinessfurniture.com": {
        "competitors": ["MNTN"],
        "vertical": "Furniture / B2B",
        "why_prospect": "309% incremental revenue growth. High-consideration product.",
    },
    # --- tvScientific ---
    "wildgrain.com": {
        "competitors": ["tvScientific"],
        "vertical": "DTC / Food Subscription",
        "why_prospect": "150% YoY subscriber growth. Subscription brand with high acquisition creative needs.",
    },
    "outer.com": {
        "competitors": ["tvScientific"],
        "vertical": "DTC / Outdoor Furniture",
        "why_prospect": "6.4x ROAS. High-consideration product brand that benefits from storytelling creative.",
    },
    "wisp.com": {
        "competitors": ["tvScientific"],
        "vertical": "Health / Telehealth",
        "why_prospect": "100.3% MoM revenue growth, 5,000 orders in first month. Fast-growing health brand.",
    },
    # --- Vibe ---
    "sijohome.com": {
        "competitors": ["Vibe"],
        "vertical": "DTC / Home Textiles",
        "why_prospect": "Scaled new customer growth with MTA. Quality-focused brand — strong Upscale ICP.",
    },
    "cyclingfrog.com": {
        "competitors": ["Vibe"],
        "vertical": "DTC / Beverages",
        "why_prospect": "678% ROAS on Vibe. Proven CTV buyer ready to scale with better creative.",
    },
    "blindster.com": {
        "competitors": ["Vibe"],
        "vertical": "Home / Window Coverings",
        "why_prospect": "14x ROAS. High-performing brand likely outgrowing template creative.",
    },
    # --- Universal Ads ---
    "palmers.com": {
        "competitors": ["Universal Ads"],
        "vertical": "Beauty / Skincare",
        "why_prospect": "Multiscreen TV campaign with The Sasha Group. Cost-efficient scale seeker.",
    },
}


# ---------------------------------------------------------------------------
# Upscale case studies with URLs and creative velocity stats
# ---------------------------------------------------------------------------

UPSCALE_CASE_STUDIES = {
    "canopy": {
        "name": "Canopy",
        "vertical": "Home / Health",
        "headline": "79% lower CPV, 53% lower CPA, 2x ROAS",
        "stats": [
            ("79%", "Lower CPV"),
            ("53%", "Lower CPA"),
            ("2x", "ROAS"),
            ("30+", "Creatives Tested"),
        ],
        "creative_story": "Modular production and structured iteration drove compounding performance gains.",
        "url": "https://upscale.ai/case-studies/scaled-creative-velocity-and-streaming-roi",
    },
    "newton": {
        "name": "Newton Baby",
        "vertical": "Baby Products",
        "headline": "80+ creatives for BFCM, 40% lower CPA",
        "stats": [
            ("80+", "Creatives Produced"),
            ("40%", "Lower CPA"),
            ("<$2", "Per Visitor"),
        ],
        "creative_story": "80+ SKU-specific variations in days. Fast-turn promo swaps in under 4 days as BFCM offers changed.",
        "url": "https://upscale.ai/case-studies/over-80-creatives-for-bfcm",
    },
    "fatty15": {
        "name": "fatty15",
        "vertical": "Health + Wellness",
        "headline": "53 creatives, 3.65x blended ROAS, 69% first-time buyers",
        "stats": [
            ("3.65x", "Blended ROAS"),
            ("69%", "First-Time Buyers"),
            ("53", "Creatives Produced"),
        ],
        "creative_story": "53 creatives across 11 unique storyboards spanning brand intro, science education, UGC, and celebrity endorsements.",
        "url": "https://upscale.ai/case-studies/turning-storytelling-into-a-growth-engine",
    },
    "lalo": {
        "name": "Lalo",
        "vertical": "Baby Products",
        "headline": "45 unique creatives, 8x faster production, 2.46x iROAS",
        "stats": [
            ("2.46x", "iROAS (verified)"),
            ("45", "Unique Creatives"),
            ("8x", "Faster Production"),
        ],
        "creative_story": "45 unique creatives across 6 marketing initiatives. Creative velocity enabled 10x internal productivity.",
        "url": "https://upscale.ai/case-studies/lalo",
    },
    "branch": {
        "name": "Branch",
        "vertical": "Furniture",
        "headline": "$50K saved on creative, 500+ purchases/month, 6.2x ROAS",
        "stats": [
            ("$50K", "Creative Savings"),
            ("6.2x", "ROAS"),
            ("500+", "Purchases/Month"),
        ],
        "creative_story": "8 new creatives included in platform cost. Winning streaming creatives expanded to YouTube and digital.",
        "url": "https://upscale.ai/case-studies/branch",
    },
}

# Creative velocity proof point — the pattern across all 5 case studies
CREATIVE_VELOCITY_PROOF = (
    "Every Upscale case study leads with creative volume: 80+ (Newton), 53 (fatty15), "
    "45 (Lalo), 30+ (Canopy), 8 (Branch). Creative velocity IS the performance lever. "
    "No competitor leads with creative volume because none of them are making the ads."
)


def get_competitor_intel(competitor_name: str) -> dict | None:
    """Get competitive intelligence for a specific competitor."""
    return COMPETITORS.get(competitor_name)


def get_creative_reality(competitor_name: str) -> dict | None:
    """Get the Creative Reality Matrix entry for a competitor."""
    return CREATIVE_REALITY_MATRIX.get(competitor_name)


def check_case_study_brand(domain: str) -> list[str]:
    """Check if a domain appears in any competitor's case studies. Returns competitor names."""
    entry = COMPETITOR_CASE_STUDY_BRANDS.get(domain.lower())
    if entry:
        return entry["competitors"]
    return []


def get_case_study_brand_intel(domain: str) -> dict | None:
    """Get full prospect intelligence for a brand in competitor case studies."""
    return COMPETITOR_CASE_STUDY_BRANDS.get(domain.lower())

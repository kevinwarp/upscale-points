# Product Requirements Document
## osmta

## 1. Overview

`osmta` is an open-source measurement operating system for ecommerce brands. It is built to help teams understand what is driving growth across paid media, owned channels, and offline activity by combining collection, identity, attribution, causal measurement, profitability analysis, and activation into one transparent platform.

Rather than acting as a narrow multi-touch attribution tool, `osmta` is designed as a unified measurement system. It separates observed business data from attributed outputs, modeled estimates, and experimentally validated lift so teams can compare different kinds of evidence without collapsing them into a single black-box metric.

The platform is modular by design. Teams can begin with the trust layer of measurement, then expand into modeled views, MMM, halo analysis, experimentation, and activation workflows over time.

## 2. Vision

Build the default open-source measurement operating system for ecommerce: a transparent, auditable, extensible system of record that helps brands make smarter budget, creative, merchandising, and profitability decisions.

## 3. Positioning

`osmta` is the open-source measurement stack for ecommerce brands that want the rigor of attribution, the strategic visibility of MMM, and the credibility of incrementality testing in one transparent platform.

## 4. Problem

Modern ecommerce measurement is fragmented across ad platforms, ecommerce systems, BI tools, finance workflows, and point solutions. Teams struggle with:

- inconsistent conversion reporting across systems
- poor identity continuity across channels and devices
- weak visibility into unattributed orders
- platform-reported performance that overstates impact
- no clean separation between correlation, attribution, modeling, and causality
- little connection between marketing measurement and actual profitability
- limited ability to activate trusted first-party measurement outputs back into execution systems

Existing vendors cover parts of this stack, but often mix different types of evidence into opaque outputs. `osmta` exists to make the full measurement process inspectable, evidence-labeled, and extensible.

## 5. Product Principles

- Every metric gets an evidence badge
- Correlation never masquerades as attribution
- Every number drills to lineage
- Order truth and journey truth remain separate but joinable
- Profitability is a core engine, not a reporting afterthought
- Activation is a separate plane, not the foundation
- AI comes after semantic rigor, lineage, and auditability are solid

## 6. Truth Framework

`osmta` organizes all outputs into four truth layers.

### 1. Observed Truth

Direct business facts and reconciled source records.

Examples:

- orders
- sessions
- clicks
- impressions
- spend
- refunds
- subscriptions
- survey responses
- product data

### 2. Attributed Truth

Rule-based or model-based fractional credit assigned to touchpoints.

Examples:

- first-touch revenue
- last-touch revenue
- linear attributed revenue
- clicks-only attribution
- clicks plus deterministic views
- clicks plus modeled views
- survey-assisted hybrid attribution

### 3. Modeled Truth

Statistical or inferred estimates of channel contribution.

Examples:

- MMM outputs
- modeled views
- survey-assisted weighting
- halo analysis

### 4. Causal Truth

Experiment-based measures of incremental impact.

Examples:

- geo lift tests
- intervention analysis
- randomized experiments
- holdout results

### Requirement

Every metric, chart, export, and API response must expose:

- evidence layer
- methodology
- model version
- attribution window if applicable
- confidence or uncertainty
- lineage to source data

## 7. Core User Promise

`osmta` should let a team answer:

- What happened?
- What was attributable?
- What was modeled?
- What was experimentally validated?
- What was profitable?
- What can we safely act on?

## 8. Product Scope

`osmta` covers five core jobs:

1. Collection
2. Identity
3. Attribution
4. Causal and modeled measurement
5. Activation

Supporting those jobs requires the following product modules:

- data collection
- order and revenue reconciliation
- identity graph and sessionization
- touchpoint builder
- attribution engine
- MMM engine
- experiment engine
- profit engine
- creative and merchandising analytics
- measurement registry
- API, UI, exports, and reverse ETL

## 9. Architecture

### High-Level Architecture

```text
Browser/Server SDKs + Shopify/Woo/Amazon/Ads connectors + Orders API + Survey SDK
                                   |
                                   v
                        Event bus + CDC + stream processing
                                   |
                    +--------------+--------------+
                    v                             v
          Raw immutable lakehouse          Hot OLAP store
        (Iceberg on object storage)       (ClickHouse)
                    |                             |
                    +--------------+--------------+
                                   v
                   Semantic models + orchestration layer
                        (dbt + Dagster + tests)
                                   |
                                   v
             Identity graph + sessionization + touchpoint builder
                                   |
        +--------------+--------------+--------------+--------------+
        v              v              v              v
   MTA engine      MMM engine   Experiment engine  Profit engine
        |              |              |              |
        +---------------------- API + UI + exports ----------------+
                                   |
                                   v
                     Reverse ETL + ad-platform writeback
```

### Data Plane Requirements

`osmta` should use a hot/cold hybrid architecture:

- Iceberg as the immutable system of record
- ClickHouse for low-latency product analytics and dashboard queries
- Debezium for CDC where source systems require row-level change capture
- Flink for stateful stream processing and event-time handling
- Dagster and dbt for orchestration, transformation, and versioned semantic models
- OpenTelemetry for logs, traces, and metrics

## 10. Canonical Data Model

Core entities include:

- `identity`: anonymous_id, device_id, click_ids, hashed_email, hashed_phone, customer_id, consent_state
- `session`: landing_source, referrer, utm values, device, geo, sequence
- `touchpoint`: click, impression, email open, email click, SMS click, affiliate click, TV/CTV exposure, influencer interaction, direct mail
- `order`: order_id, source_system, timestamp, revenue, tax, shipping, discount, refund_reserve, channel_source
- `order_line`: sku, product, quantity, item_revenue, item_margin
- `campaign_graph`: channel, campaign, ad_set, ad, creative, objective
- `survey_response`: post-purchase answer, confidence flags, bias flags
- `experiment`: test cell, control cell, geography, pre-period, post-period, metrics

### Dual Truth Requirement

The platform must preserve:

- `order_truth`: the server-side business record of the conversion
- `journey_truth`: the touchpoint chain that may explain the conversion

These must remain separate but joinable. An order can exist without a valid journey chain, and unattributed orders must be explainable rather than hidden.

## 11. Functional Requirements

### 11.1 Collection Layer

`osmta` must support:

- browser SDKs
- server SDKs
- Orders API ingestion
- Shopify and WooCommerce sync
- survey collection SDKs
- ad platform and marketplace connectors
- event deduplication
- schema validation
- consent-aware collection handling
- ingestion health monitoring

### 11.2 Identity Layer

`osmta` must:

- stitch anonymous and known identities
- join device, click, session, and customer records
- support deterministic and configurable probabilistic matching
- preserve consent state
- expose match confidence and match reason
- version identity logic
- support merge and split correction workflows

### 11.3 Sessionization and Touchpoint Builder

`osmta` must:

- construct sessions from raw event streams
- normalize referrer, UTM, and click metadata
- create ordered touchpoint chains per identity
- support impression, click, owned-channel, and offline touchpoint types
- define eligibility windows for downstream attribution

### 11.4 Attribution Engine

The attribution engine must be plugin-based, not hard-coded.

Initial supported models:

- first touch
- last touch
- last non-direct
- linear
- clicks-only
- clicks plus modeled views
- clicks plus deterministic views
- survey-assisted hybrid

Each attributed output must retain:

- `evidence_type = deterministic | modeled | survey_assisted`
- attribution model
- lookback window
- confidence score
- model version

Each attributed order must also store:

- eligible touchpoints
- excluded touchpoints
- precedence rules
- unattributed reason code if applicable

### 11.5 Halo Analysis

`osmta` must support a distinct halo analysis workflow for lagged correlation across channels such as:

- TV
- podcasts
- DOOH
- influencer
- direct mail

Halo outputs must never be booked as attributed revenue. They must be explicitly labeled as modeled or correlational evidence.

### 11.6 MMM Engine

Rather than a single proprietary model, `osmta` should provide a wrapper layer over OSS MMM engines.

Planned engine integrations:

- Robyn
- Meridian
- PyMC-Marketing

Requirements:

- unified run interface
- standardized diagnostics and metadata capture
- budget planning and scenario analysis
- geo-level support where relevant
- calibration hooks to lift studies when available

### 11.7 Experiment Engine

`osmta` must support three experimentation tracks:

- on-site or product experiments via GrowthBook
- geo-based incrementality via GeoLift
- intervention analysis via CausalImpact

The engine must support:

- test definition
- control/treatment structure
- metric selection
- pre/post period management
- confidence intervals
- archived results and diagnostics

### 11.8 Measurement Registry

A shared measurement registry is a core requirement.

Every attribution run, MMM run, geo test, and intervention analysis must write into the registry with:

- model inputs
- assumptions
- priors if applicable
- diagnostics
- calibration status
- confidence bands
- evidence layer
- version metadata

This registry becomes the canonical place for the UI and APIs to determine whether a number is observed, inferred, or experimentally validated.

### 11.9 Profit Engine

Profitability must be a first-class system component.

The profit engine must join:

- orders and order lines
- COGS and landed costs
- shipping and fulfillment
- payment fees
- discounts and refunds
- subscription renewals and churn
- attributed and blended spend

Default outputs should include:

- contribution margin
- CAC
- MER
- payback period
- refund-adjusted revenue
- SKU-level attributed revenue
- SKU-level attributed spend
- benchmark thresholds

The platform should support benchmark logic such as:

- max blended CAC for a target payback window
- minimum ROAS required to maintain target margin thresholds

### 11.10 Product and Creative Analytics

`osmta` must:

- attribute and model performance at the SKU and product level
- support product hierarchy rollups
- compute creative fingerprints and creative-level performance views
- connect spend and creative decisions to merchandising and profitability outcomes

### 11.11 Activation Plane

Activation must remain a separate plane from the core measurement system.

It must support:

- reverse ETL audiences
- warehouse exports
- conversion feeds
- ad-platform writeback adapters
- sync monitoring and failure logging

Vendor-specific feedback loops should be built as optional adapters with clean contracts so the core product remains usable even when partner APIs are limited.

## 12. UX Requirements

The UI must preserve the distinction between truth layers at all times. It should never present modeled or correlational outputs as if they are deterministic conversion truth.

Core UX surfaces:

- executive dashboard
- order truth and journey truth explorer
- unattributed order audit
- attribution model comparison
- touchpoint-level order audit trail
- MMM workspace
- halo explorer
- experiment workspace
- profit benchmarks dashboard
- product and creative analytics
- measurement registry and lineage explorer
- activation center

## 13. Key Differentiators

`osmta` differs from category incumbents by making the following product rules explicit:

- every metric carries an evidence badge
- correlation is kept separate from attribution
- unattributed orders are first-class and queryable
- every number can be traced to source tables, model version, exclusions, and windows
- the semantic and audit layer comes before any AI assistant layer

## 14. Phased Delivery

### Phase 1: Trust Layer

Ship:

- pixel and server SDKs
- Shopify and WooCommerce orders sync
- identity graph
- clicks-only attribution
- first-touch, last-touch, and linear models
- unattributed order audit
- profit-aware executive dashboard

### Phase 2: Measurement Layer

Ship:

- modeled views
- survey-assisted hybrid attribution
- MMM wrapper layer
- halo explorer
- product analytics
- creative analytics
- model comparison UI

### Phase 3: Causal and Activation Layer

Ship:

- GeoLift and CausalImpact workflows
- calibration registry
- reverse ETL audiences
- ad-platform writeback adapters
- deterministic-view integrations where partner access exists

## 15. MVP Recommendation

The initial wedge should be:

- order truth
- journey truth
- model comparison
- unattributed audit
- profit benchmarks

This is the smallest credible version of `osmta` that produces immediate user trust and creates a clean foundation for harder modules later.

## 16. Success Metrics

Track success across four dimensions.

### Product Adoption

- time to first trustworthy dashboard
- number of connected sources
- weekly active workspaces
- percent of users engaging with model comparison

### Measurement Quality

- percent of orders reconciled
- percent of orders with explainable attribution status
- discrepancy reduction across platform reports and `osmta`
- percent of metrics carrying lineage and evidence labels

### Profitability Usage

- adoption of profit-aware views
- use of benchmark builder outputs
- number of teams using CAC, MER, and payback metrics operationally

### Platform Ecosystem

- open-source contributors
- plugin and connector contributions
- self-hosted deployments
- third-party engine integrations

## 17. Risks

Key risks:

- building too much breadth before trust is earned
- source data quality undermining downstream outputs
- complexity of explaining deterministic vs modeled vs causal evidence
- vendor-specific integrations limiting parity in activation or deterministic views
- architecture complexity increasing implementation time for the open-source community

## 18. Summary

`osmta` is not just an attribution tool. It is a unified open-source measurement operating system for ecommerce that keeps observed truth, attributed truth, modeled truth, and causal truth explicitly separate. Its foundation is dual conversion truth, a plugin-based attribution layer, a shared measurement registry, and a profit-aware measurement model. The product should start by earning trust through order truth, journey truth, model comparison, unattributed audits, and profit benchmarks, then expand into MMM, experimentation, and activation on top of that foundation.

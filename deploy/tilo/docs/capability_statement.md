# AXIOM Capability Statement
## Nexxon National | Unclassified | For Official Use Only

---

### Company

**Nexxon National** is a defense technology company and subsidiary of Blackthorne Group,
focused on AI-enabled command and control solutions for special operations forces.
Nexxon National is a participant in the BVVC School.House accelerator program.

---

### Platform

**AXIOM** (Adaptive eXecution Intelligence for Operations Management) is an
AI-assisted mission command platform designed for special operations forces operating
in complex, denied, and contested environments.

---

### Core Capabilities

**1. AI Mission Replanning**
Real-time course of action generation when threats emerge or conditions change.
AXIOM analyzes the tactical situation and produces multiple COAs with risk assessment
and tactical rationale in under 3 milliseconds. Supports both cloud AI and
offline local model operation for denied environments.

**2. Geospatial Intelligence Layer**
Live threat overlay rendering with confidence-weighted radius visualization.
Route geometry engine calculates segment distances and operational area bounding.
GeoJSON output compatible with MapLibre GL, ATAK, and all standard GIS systems.

**3. ROE-Gated Target Management**
Priority scoring engine using weighted tactical factors: threat level (35%),
intelligence confidence (25%), proximity to friendly forces (20%), target type (15%),
time sensitivity (5%). ROE compliance evaluated automatically on nomination.
PROHIBITED status cannot be overridden by any user or role.

**4. Multi-Form-Factor Display System**
Same mission state delivered optimally to any device:
- Ruggedized tablet: full tactical picture, all layers
- HUD: 6 fields maximum, 1-second refresh, night-vision compatible
- Wrist device: 3-field micro payload (GO/HOLD/ABORT + threats + action)

**5. FIPS 140-2 Compliant Encryption**
AES-256-GCM authenticated encryption with HMAC-SHA256 message signing.
Mission-scoped key derivation. Tamper-evident audit chain.
Architecture supports HSM and KMS integration.

**6. Role-Based Access Control**
Six-tier hierarchy mapping to SOF command structure:
System > Commander > Staff > ISR > Operator > Observer.
Designed for CAC/PIV card integration.

---

### Differentiators

| Capability | Market | AXIOM |
|---|---|---|
| AI mission replanning | Fragmented / manual | Unified, <3ms |
| Threat-reactive routing | Separate GIS tools | Integrated |
| ROE guardrails | Analyst-dependent | Automated |
| Form factor flexibility | Single device | HUD to wrist |
| Offline AI | None at edge | Local model ready |
| Audit trail | Fragmented | Tamper-evident chain |

---

### Technology Readiness

Current TRL: 4 (Lab validation complete)
Target TRL: 6 (Prototype demonstration) — BVVC pitch milestone
Path to TRL 9: TILO sandbox -> AFSOC pilot -> perpetual contract

---

### Target Customers

- AFSOC (Air Force Special Operations Command)
- USSOCOM (United States Special Operations Command)
- Naval Special Warfare Command
- 75th Ranger Regiment
- MARSOC

---

### Contact

**Nexxon National**
A Blackthorne Group Company
GitHub: github.com/nexxondev/axiom
Accelerator: BVVC School.House

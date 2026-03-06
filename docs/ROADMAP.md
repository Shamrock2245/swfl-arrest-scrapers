# ROADMAP.md - Strategic Goals & Expansion

This file tracks the "Blinking Lights" (High Priority / Growth Engines) for the SWFL Arrest Scrapers platform.

## 🚨 Blinking Lights (Immediate Focus)

### 1. "The Scout" Expansion (Geographic Rollout)
*   **Objective**: Expand coverage to 5 new county jails to increase lead volume without requiring additional staff.
*   **Status**: In Progress
*   **Actions Required**:
    *   Identify target counties and their booking roster tech stacks.
    *   Adapt "The Clerk" to monitor and scrape these 5 new endpoints daily.
    *   Ensure all new scrapers output exactly to the standardized 34-column schema.

### 2. WhatsApp Business Integration
*   **Objective**: Reach clients globally where open rates are highest.
*   **Status**: Pending Configuration
*   **Actions Required**:
    *   Enable Twilio Sandbox.
    *   Wire the Twilio integration to `twilio-client.jsw` securely.

### 3. "The Closer" Bot (Follow-up Automation)
*   **Objective**: Convert leads who have dropped off during the intake process.
*   **Status**: Pipeline
*   **Actions Required**:
    *   Build automated SMS/WhatsApp drip campaigns targeted at abandoned intakes.

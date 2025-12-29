---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments: ["product-brief-ResiPlanAI-2025-12-29.md"]
workflowType: 'prd'
lastStep: 11
briefCount: 1
researchCount: 0
brainstormingCount: 0
projectDocsCount: 0
---

# Product Requirements Document - ResiPlanAI

**Author:** Amit
**Date:** 2025-12-29

## Executive Summary

ResiPlanAI (Phase 1) is a specialized B2B SaaS platform designed to solve the "Scheduling Tetris" of Obstetrics and Gynecology residency programs. It features a powerful **Constraint Satisfaction Engine** that automates the creation of valid 72-month (Model A) and 66-month (Model B) residency plans. The system serves as a "One-Click Compliance" tool for Program Directors, ensuring that every generated schedule strictly adheres to individual syllabus requirements, rigid ward staffing capacities, and immutable historical data.

### What Makes This Special

Unlike generic scheduling tools, ResiPlanAI is purpose-built for the rigid, multi-year complexity of medical residency. Its core differentiator is the **"Anchor-Aware Solver"**—a dynamic engine that allows managers to manually lock specific rotations ("Anchors") and instantly re-calculates the entire remaining 6-year matrix to maintain compliance with "Stage A/B" exam windows and ward quotas. It solves the "Ripple Effect" of disruptions (like maternity leave) in milliseconds, ensuring audit-ready compliance without manual calculation.

## Project Classification

**Technical Type:** `saas_b2b` (Responsive Web App)
**Domain:** `healthcare` (Workforce Management)
**Complexity:** `high` (Due to Constraint Satisfaction Problem (CSP) logic and Audit requirements)
**Project Context:** Greenfield - new project (Phase 1 focus)

### Critical Scope Pivot
**Phase 1 Focus:** This PRD covers **ONLY** the Residency Program Agent (Scheduler). The Clinical Companion (Agent 2) is explicitly deferred to Phase 2.

## Success Criteria

### User Success

#### The "Audit-Proof" Peace of Mind
*   **Outcome:** The Program Director trusts the system to catch subtle, complex violations that humans miss (e.g., "Stage A" window vs. Ward Capacity).
*   **Success Moment:** When the system proactively blocks or warns against a manual move that would inadvertently break a 3-year-out regulatory deadline.
*   **Metric:** **0% "Impossible" Schedules.** The system never allows a "Valid" state that violates a hard constraint.

### Business Success

#### 100% Reliance (Zero Parallel Excel)
*   **Goal:** The Scheduler becomes the *only* source of truth.
*   **Anti-Pattern:** If the manager maintains a "Backup Excel," we have failed.
*   **Target:** Within 3 months of deployment, the Program Director ceases all manual scheduling in parallel tools.

### Technical Success

#### The Constraint Engine Performance
*   **Immediate Conflict Detection (< 1s):** Dragging a resident to an invalid slot (e.g., Year 1 resident in Year 6 slot) triggers an instant UI warning.
*   **Full Matrix Solution (< 10s):** After setting "Anchors," the engine solves the remaining 72-month x 40-resident matrix to satisfy all Ward Capacity and Syllabus constraints within 10 seconds.
*   **Stability:** The solver consistently finds a solution if one exists, or clearly identifies *why* a solution is impossible (e.g., "Conflict: Not enough residents to staff IVF").

## Product Scope

### MVP - Minimum Viable Product (Phase 1)

#### 1. The Constraint Satisfaction Engine (Backend)
*   **Logic:** Handles 72-month (Model A) and 66-month (Model B) rules.
*   **Hard Constraints:**
    *   **Syllabus:** Stage A/B windows, Consecutive IVF (6mo), Department A/B partitioning.
    *   **Ward Capacity:** Min/Max per ward per month (e.g., Delivery Room 3-4, IVF 2-4).
    *   **History:** "Immutable Past" logic (cannot change < Current Month).
*   **Anchor Logic:** Treats manual placements as infinite-weight constraints and solves around them.

#### 2. The Management Dashboard (Frontend)
*   **God View:** A responsive web grid showing 40+ residents x 72 months.
*   **Anchor Tools:** UI to lock/unlock specific slots.
*   **Conflict Visualization:** Instant visual feedback (Red/Green) for constraint violations.
*   **Audit Export:** PDF generation for Scientific Council compliance.

### Vision (Future - Phase 2)
*   **Agent 2 (Clinical Companion):** The Resident App with Contextual Learning and "Safety Shields."
*   **Automated Shift Trading:** Resident-to-resident swap marketplace with syllabus validation.

## User Journeys

### Journey 1: Dr. Elana - Reclaiming the Weekend
Dr. Elana is the Program Director. It’s Friday afternoon, and a senior resident just notified her of a 6-month maternity leave (HLD) starting next month. Normally, Elana would spend her entire Saturday with three highlighters and a giant Excel sheet, manually shifting 40 people to ensure the Delivery Room isn't empty in July.

She opens ResiPlanAI, enters the leave dates for the resident, and hits "Resolve." The system highlights three capacity conflicts in red. Elana moves an "Anchor" for a junior resident to cover the July gap. The engine immediately ripples through the next 2 years, confirming that this move doesn't push that junior resident out of their "Stage A" exam window. She clicks "Approve," and a year's worth of planning is updated in 5 minutes. She closes her laptop and goes home for the weekend.

### Journey 2: Dr. Amir - The "Aha!" Moment of Trust
Amir is a Station Manager (Head of IVF). He’s skeptical of the new "AI" scheduler. He logs into his "Ward View" and sees that for October, he only has 1 resident assigned, even though his minimum is 2. He prepares an angry email to Elana. 

However, he notices a "Conflict" flag on the slot. He clicks it, and the system explains: *"Syllabus Rule Violation: Resident X cannot be moved to IVF in October because they must complete their mandatory ER rotation before their Stage B exam in November."* Amir realizes the system caught a regulatory constraint he had forgotten. He stops typing the email, realizing the system is protecting the resident's career.

### Journey 3: The Auditor - The "Stress-Free" Review
A representative from the Scientific Council arrives for a bi-annual audit. They ask for the residency path of "Resident Y." In the past, this meant digging through paper files and disparate spreadsheets.

Elana clicks "Export for Audit" in ResiPlanAI. A clean, professional PDF is generated, showing Resident Y's 72-month path, with every rotation clearly mapped to a syllabus requirement. It highlights that all 6 months of IVF were consecutive and that "Stage A" requirements were met. The auditor signs off in 10 minutes, impressed by the transparency and lack of errors.

### Journey Requirements Summary
These journeys reveal the need for:
*   **Dynamic CSP Engine:** Handling the "Ripple Effect" and "Anchor" logic (Elana's journey).
*   **Constraint Explanation UI:** Don't just show a "Red" slot; explain *why* it's red (Amir's journey).
*   **Audit Export Module:** Highly formatted PDF generator with regulatory mapping (The Auditor's journey).
*   **Role-Based Access Control (RBAC):** "Program Director" (Edit) vs. "Station Manager" (View/Warn) (Amir's journey).

## Domain-Specific Requirements

### Healthcare Compliance & Regulatory Overview
ResiPlanAI operates in a high-stakes clinical environment where scheduling errors can lead to two critical failures:
1.  **Regulatory Failure:** A resident is disqualified from board exams because their schedule violated Scientific Council rules (e.g., missed Stage A window).
2.  **Safety Failure:** A ward is understaffed below critical minimums, compromising patient care.

### Key Domain Concerns
*   **Scientific Council Alignment:** The system's logic must be a perfect mirror of the "Model A/B" syllabus regulations.
*   **Patient Safety via Staffing:** Ward capacity is not just a number; it's a safety metric.
*   **Auditability:** Every schedule must be traceable and verifiable by external auditors.

### Compliance Requirements
*   **Configurable Rule Engine:** The "Syllabus" (rotation lengths, exam windows) must be stored as versioned configuration data, editable by Admins, not hard-coded. This ensures long-term compliance as regulations evolve.
*   **Audit-Ready Reports:** The system must generate PDF exports that specifically visualize the "Critical Anchors" (Stage A window, Stage B window, Syllabus Completeness) to prove validity to the Council.

### Implementation Considerations
*   **Hard vs. Soft Constraints:**
    *   **Hard Constraint (Safety Floor):** Absolute minimum staffing (e.g., HRP < 1). Violation blocks the schedule or requires "Force Override" with a logged reason.
    *   **Soft Constraint (Optimization Target):** Preferred staffing range (e.g., Delivery Room 4). The solver prioritizes this but allows the "Hard Minimum" (e.g., 3) if necessary to satisfy other rules.
*   **Validation Layer:** A dedicated background service that continuously checks every resident's timeline against the active "Rule Engine" configuration, flagging any discrepancies instantly.

## Innovation & Novel Patterns

### Detected Innovation Areas

#### 1. The "Anchor-First" Solver (Core Differentiator)
*   **Concept:** A hybrid scheduling paradigm where Human Discretion > Algorithm. The Manager sets "Anchors" (fixed manual placements), and the AI treats them as infinite-weight constraints, solving the rest of the 72-month matrix around them.
*   **Why It's Novel:** Most schedulers are either fully manual (Excel) or "Black Box" optimization. ResiPlanAI creates a collaborative dynamic where the human sets the strategy and the AI handles the logistics.

#### 2. The "Elastic Timeline" Engine
*   **Concept:** A dynamic duration logic that adapts to life events.
*   **Innovation:** The system distinguishes between "Absence within Syllabus" (reducing elective time) vs. "Residency Extension" (pushing the end date).
*   **Ripple Effect:** A single HLD input triggers a real-time re-calculation of the resident's entire future timeline, validating "Stage A/B" exam windows against the new completion date.

#### 3. Departmental Parallelism (Dual-Track Optimization)
*   **Concept:** Solving for two distinct cohorts (Department A & B) that compete for shared resources (Delivery Room, IVF).
*   **Innovation:** The CSP engine runs parallel optimization tracks for Dept A and B logic while simultaneously satisfying the aggregate capacity constraints of the shared wards.

### Validation Approach
*   **The "Anchor Test":** We will stress-test the solver by placing conflicting Anchors (e.g., locking a Year 1 resident into a Year 4 slot) and verifying the system's ability to either solve around it or clearly explain *why* it's impossible.
*   **The "Ripple Test":** Inputting a 6-month leave in Year 2 and verifying that the system correctly shifts the "Stage A" window and extends the completion date without breaking ward capacity.

### Risk Mitigation
*   **Complexity Risk:** The "Elastic Timeline" could create unsolveable scenarios.
*   **Mitigation:** We will implement clear "Conflict Resolution" UI that suggests *which* Anchor to move if the puzzle becomes impossible.

## SaaS B2B Specific Requirements

### Project-Type Overview
ResiPlanAI is deployed as a specialized B2B platform for healthcare workforce management. While initially targeting a single hospital deployment, the architecture will be designed to support future multi-tenant scaling.

### Technical Architecture Considerations
*   **Tenancy Model:** Single-hospital focus for MVP. Data isolation will be enforced at the schema level to facilitate future multi-tenant migration.
*   **Authentication & Authorization:**
    *   **Method:** Managed User Accounts (Email/Password).
    *   **Authorization:** Role-Based Access Control (RBAC) with three primary levels:
        1.  **Program Director (Super Admin):** Full write access to all resident schedules and global rule configuration.
        2.  **Station Manager (Ward Admin):** View access to all residents; Write access to specific "Ward Roster" validation.
        3.  **Resident (User):** View-only access to their personal 72-month timeline and shift partners.

### Compliance Requirements
*   **Data Retention:** The system must preserve the complete "Audit Trail" for every resident from their start date to their graduation (standard 6-7 years). 
*   **The "Immutable Record":** Once a month passes from the "System Clock," the data for that month is locked and cannot be edited, serving as a historical record for Scientific Council audits.

### Implementation Considerations
*   **Email-Based Identity:** Use unique email addresses as the primary identifier for residents and managers.
*   **Scaling Path:** Design the database with a `HospitalID` column from Day 1 to ensure that adding "Hospital #2" next year is a configuration change rather than a refactor.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving MVP
**Resource Requirements:** Requires 1 Senior Backend Engineer (Optimization/CSP focus), 1 Frontend Engineer (Grid/Data Viz focus), and 1 Domain Expert (Syllabus Specialist).

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Journey 1: Reclaiming the Weekend (The Director)
- Journey 3: The "Stress-Free" Review (The Auditor)

**Must-Have Capabilities:**
- **The Engine:** Logic for 72/66-month Models, Ward Capacities, and Syllabus Windows.
- **Interactive Grid:** god-view with manual "Anchor" locking/unlocking.
- **Conflict Logic:** Instant Red/Green validation and conflict explanation.
- **Audit Export:** Professional PDF generation for Scientific Council submission.
- **Basic RBAC:** Program Director (Edit) vs. Ward Manager (View).

### Post-MVP Features

**Phase 2 (Post-MVP):**
- **Resident AI Companion:** The context-aware clinical guide and micro-learning feed.
- **Safety Shield:** Explicit conflict widget for Israeli vs. International standards.
- **Shift Trading:** Automated, rule-validated swap marketplace.

**Phase 3 (Expansion):**
- **Multi-Tenancy:** Scaling the architecture to support multiple hospitals.
- **Advanced Analytics:** Predicting future staffing shortages and rotation bottlenecks 2-3 years in advance.

### Risk Mitigation Strategy

**Technical Risks:** The complexity of the "Ripple Effect" calculation. **Mitigation:** We will implement a "Greedy Solver" approach initially that handles hard constraints first, allowing the human to resolve soft conflicts manually if the AI stalls.
**Market Risks:** Lack of trust in AI-generated compliance. **Mitigation:** The "Audit Export" is the proof. By visualizing the *rules* alongside the *slots*, we build transparency and trust.
**Resource Risks:** Complexity of medical regulations. **Mitigation:** Keep the "Syllabus" as a versioned config file, allowing the user to tweak rules without a developer deployment.

## Functional Requirements

### Scheduling Logic & Constraint Satisfaction

- FR1: The System can calculate valid 72-month (Model A) and 66-month (Model B) residency plans for 40+ residents simultaneously.
- FR2: The System can enforce hard constraints for syllabus completion (e.g., Stage A/B windows, mandatory ward rotations).
- FR3: The System can enforce ward capacity constraints (min/max staffing per ward per month).
- FR4: The System can calculate the "Ripple Effect" on future rotations when a life event (e.g., HLD, maternity leave) is recorded.
- FR5: The System can distinguish between "Absence within Syllabus" (deducting elective time) and "Residency Extension" (pushing the graduation date).
- FR6: The System can treat manually locked slots ("Anchors") as fixed constraints during automated re-calculation.

### Management Dashboard & God View

- FR7: Program Directors can view a comprehensive grid of all residents across the 72-month timeline.
- FR8: Program Directors can manually lock ("Anchor") or unlock specific rotation slots for any resident.
- FR9: Program Directors can input and update resident metadata (e.g., start date, department assignment A or B).
- FR10: Program Directors can trigger a "Resolve" command to re-calculate the entire schedule based on new constraints.
- FR11: Program Directors can override a "Hard Constraint" violation with a mandatory justification log.

### Conflict Visualization & Audit

- FR12: The System can display real-time visual feedback (Red/Green) for all constraint violations in the grid.
- FR13: The System can provide a specific explanation for why a slot is in conflict (e.g., "Syllabus Rule Violation: Missed Stage A window").
- FR14: The System can generate a Scientific Council-compliant PDF export of a resident's complete path.
- FR15: The System can preserve an immutable record of historical scheduling data once a month has passed.

### Access Control & History

- FR16: The System can restrict "Edit" access to the schedule to authenticated Program Directors.
- FR17: The System can provide "View-Only" access to Station Managers for their respective ward staffing rosters.
- FR18: Residents can view their own personal 72-month timeline and shift partners.
- FR19: The System can maintain an audit trail of all manual changes made to the schedule, including who made the change and when.

### System Configuration

- FR20: Administrators can update the "Syllabus Rule Engine" configuration (e.g., changing a mandatory rotation length) without modifying code.
- FR21: Administrators can define and update Ward Capacity limits (Min/Max) for all clinical stations.

## Non-Functional Requirements

### Performance

- **Conflict Detection:** Visual feedback for a single manual move (Anchor) must be updated in the UI in less than 1 second.
- **Full Matrix Resolve:** The CSP solver must find a valid 72-month solution for 40 residents in less than 10 seconds.
- **Report Generation:** PDF exports for the Scientific Council must be generated in less than 5 seconds.

### Security

- **Encryption:** All resident data (including PII like names and ID numbers) must be encrypted at rest (AES-256) and in transit (TLS 1.2+).
- **Authentication:** Access must be secured via email-based identity with support for mandatory password complexity rules.
- **Session Management:** Sessions for Program Directors must automatically timeout after 30 minutes of inactivity to prevent unauthorized access in clinical areas.

### Reliability & Trust

- **Data Integrity:** The system must guarantee that "Anchors" (manual locks) are never moved by the automated solver.
- **Error Handling:** If the solver cannot find a valid solution, it must provide a "Reason Code" identifying the specific conflicting constraints within 2 seconds.
- **Consistency:** The system must ensure that the "System Clock" correctly locks historical data, making it immutable after the current month.

### Auditability & Compliance

- **Traceability:** Every manual override of a hard constraint must be logged with a timestamp, the user ID of the Program Director, and a mandatory text justification.
- **Version Control:** The "Syllabus Rule Engine" configuration must support versioning, allowing the system to prove which rules were in effect at any point in the historical record.

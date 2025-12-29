---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
date: 2025-12-29
author: Amit
---

# Product Brief: ResiPlanAI

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

ResiPlanAI is a dual-agent system designed to revolutionize the Obstetrics and Gynecology residency experience by solving the twin challenges of administrative complexity and educational disconnect. The platform consists of two synchronized agents: the **Residency Program Agent**, which automates the creation of compliant 6-year residency schedules amidst rigid syllabus and staffing constraints, and the **Resident AI Companion**, an adaptive learning tool that delivers hyper-relevant study materials based on the resident's real-time location and seniority. By bridging the gap between scheduling logistics and clinical education, ResiPlanAI ensures administrative compliance while reducing resident burnout through context-aware, conflict-resolving educational support.

---

## Core Vision

### Problem Statement

The residency ecosystem is failing on two fronts. Administratively, Program Directors struggle to manually align rigid individual 72-month syllabus requirements with strict ward staffing capacities and inevitable life disruptions (maternity leave, unpaid leave). Educationally, residents suffer from a "disconnect" where study materials are irrelevant to their daily clinical reality, and they face confusion from conflicting medical standards (International textbooks vs. Local Israeli position papers).

### Problem Impact

*   **For Administrators:** Countless hours lost to manual scheduling tetris, risk of non-compliant residency completion, and staffing gaps in critical wards.
*   **For Residents:** Increased burnout due to inefficient study time, cognitive load from reconciling conflicting medical protocols, and "wasted" downtime that could be used for micro-learning.

### Why Existing Solutions Fall Short

Current solutions are siloed. Scheduling tools lack the nuance of syllabus sequencing and ward capacity balancing, while educational apps are "blind" to the resident's specific context (rotation, seniority, exam timeline), delivering generic content that adds noise rather than value.

### Proposed Solution

**ResiPlanAI** delivers a synchronized dual-agent ecosystem:
1.  **Residency Program Agent (Scheduler):** An intelligent constraint-solver that generates valid 72-month plans, dynamically balancing individual syllabus needs against ward capacities and instantly adapting to life disruptions.
2.  **Resident AI Companion (Clinical):** A context-aware guide that filters study materials based on the resident's exact rotation and seniority. It features a "Micro-learning" engine for downtime and an explicit "Conflict Resolver" for international vs. local medical standards.

### Key Differentiators

*   **Contextual Intelligence:** The Clinical Companion is powered by the Scheduler's real-time data, ensuring 100% relevance of study materials.
*   **Conflict Resolution:** Unique focus on bridging the gap between International Textbooks and Local Position Papers.
*   **Exam Readiness:** Automatic adjustment of learning intensity based on the Scheduler's awareness of approaching Stage A/B exams.

---

## Target Users

### Primary Users

#### 1. The Management Team (Program Directors & Department Heads)
*   **Role:** The architects and guardians of the residency program. They are responsible for the operational staffing of all wards and the academic validity of every resident's 6-year path.
*   **Context:** Dealing with constant resource constraints. They need to ensure the ER is staffed tonight while ensuring "Dr. Cohen" finishes her Ultrasound rotation before her exams next year.
*   **Pain Points:** "Scheduling Tetris." The cognitive load of balancing individual syllabus requirements against ward capacities and unexpected leaves (maternity, illness) is overwhelming.
*   **Success Vision:** A "One-Click Compliance" dashboard. They want to see a holistic view of the 72-month program where green means "Staffed & Compliant" and red highlights specific conflicts to resolve. They need to approve/override the agent's suggestions.

#### 2. The Resident (Junior to Senior)
*   **Role:** The clinical workforce and learner. They rotate through wards for 6 years, evolving from novice to expert.
*   **Context:** High-stress, time-poor environment. They need to know where they need to be, who they are working with, and what they need to know *right now*.
*   **Pain Points:** "Noise." They are bombarded with general medical info that doesn't fit their specific rotation or seniority level. They struggle to find time to study valid materials.
*   **Success Vision:** A "Personal Companion." They open the app and see:
    *   **Logistics:** My schedule for this month, my shift partners for today.
    *   **Education:** The specific syllabus for *this* rotation.
    *   **AI Coach:** Study materials tailored to my exact seniority (e.g., "Basics of IVF" for Year 1 vs. "Advanced Protocols" for Year 5) and specifically resolving conflicts between international texts and local position papers.

### User Journey

#### The Management Journey (Macro-Control)
1.  **Input:** Program Director enters/updates constraints (e.g., "Dr. Levi is on HLD for 3 months").
2.  **Generation:** The **Residency Program Agent** generates a revised 72-month matrix for all 40 residents, respecting all syllabus rules and ward quotas.
3.  **Review:** Director sees a "God View" dashboard highlighting any staffing gaps or syllabus risks.
4.  **Approval:** Director approves the plan. The schedule is published to residents.

#### The Resident Journey (Micro-Focus)
1.  **Context:** Resident opens the app at the start of a shift in the Delivery Room.
2.  **Logistics:** Sees "Today: Delivery Room with Dr. X and Dr. Y."
3.  **Learning:** The **Resident AI Companion** pushes a 5-minute micro-learning module: "Local Position Paper: Management of PPH," relevant to the Delivery Room and their current Year 2 status.
4.  **Growth:** Resident tracks their progress against the syllabus: "Rotation 4/72 complete. Stage A exam in 8 months."

---

## Success Metrics

### User Success Metrics

#### For Management: The "Sanity" Metric (0% Manual Override)
*   **Goal:** The Program Director defines the constraints ("anchors") and the agent generates the rest.
*   **Metric:** **Manual Override Rate.** We aim for <5% overrides on AI-generated schedules. If the director has to manually fix valid generated slots, the trust is broken.
*   **Outcome:** "Click & Done" scheduling for complex 72-month matrices.

#### For Residents: The "Utility" Metric (Engagement During Shifts)
*   **Goal:** Residents utilizing "dead time" for relevant learning.
*   **Metric:** **Shift-Time Daily Active Users (DAU).** Tracking engagement with the app *during* clinical hours (not just at home).
*   **Outcome:** Bridging the gap between theory and practice in real-time.

### Business & Institutional Objectives

#### 1. Audit-Readiness (Regulatory Compliance)
*   **Objective:** Ensure every resident's schedule is legally valid for board exam qualification.
*   **Metric:** **100% Audit Pass Rate.** The system's "Export for Audit" report must be accepted by the Scientific Council/Regulators without modification.
*   **Risk Mitigation:** The system prevents "hallucinated" rotations or miscalculated leave time (HLD/HLT) that could disqualify a resident.

#### 2. Clinical Safety Compliance
*   **Objective:** Ensure residents follow Local Position Papers over conflicting International Textbooks.
*   **Metric:** **Conflict Resolution Success Rate.** Measured by quiz performance on topics with known conflicts (e.g., PPH management). We want to see knowledge gaps ("Red" on the heatmap) turn "Green" specifically on these critical safety protocols.

### Key Performance Indicators (KPIs)

*   **Scheduling Efficiency:** Reduction in time spent on monthly schedule generation (Target: <30 minutes vs. days).
*   **Syllabus Adherence:** 100% of residents reaching Year 6 with all mandatory rotations completed.
*   **Micro-Learning Adoption:** Avg. 3+ micro-learning sessions per resident per week during shift hours.

---

## MVP Scope

### Core Features

#### 1. The Residency Program Agent (Scheduler)
*   **Constraint Solver Engine:** Automates 72-month (Model A) or 66-month (Model B) personal plans for 40+ residents. 
    *   **Hard Constraints:** Syllabus sequencing, rigid ward capacity limits, and "Immutable Past" (cannot change data from the current month backward).
    *   **Continuity Logic:** Consecutive 6-month IVF rotations; preferred continuity for HRP, Delivery, and Gyn.
    *   **Department Split:** Logical partitioning of HRP/Gyn rotations based on "Department A" or "B" assignment.
*   **Management Dashboard:**
    *   **Input & Anchors:** Interface to set start dates, leaves (HLD/HLT), and "Fixed Date" anchors that the AI cannot move.
    *   **God View Matrix:** Visual 72-month grid with "Future Bottleneck" warnings for ward capacity.
    *   **Export for Audit:** One-click regulatory-compliant reports proving syllabus adherence for board exam qualification.

#### 2. The Resident AI Companion (Clinical)
*   **Context-Aware Home Screen:** Automatically displays current Ward, Seniority, and Shift Partners based on the Scheduler's data.
*   **The Conflict Box (Safety Shield):** A prominent Red Box widget that explicitly highlights discrepancies where Israeli Position Papers override International Textbooks.
*   **Closed-Garden RAG Engine:** Strict retrieval-only answers from indexed PDFs/Textbooks. If the source is missing, the agent explicitly states "Topic not in defined sources."
*   **Micro-Learning Feed:** Bite-sized infographics/PDFs filtered by the resident's current rotation and Stage A/B exam timeline.

### Out of Scope for MVP
*   **Daily Shift Scheduling:** Monthly rotations only; no nightly/daily shift allocation.
*   **Automated Swapping:** No resident-to-resident trade marketplace or AI-validated trades.
*   **External Integrations:** No live connection to hospital EMR or patient data.
*   **Social & Mock Exams:** No community features or full-blown exam simulations.

### MVP Success Criteria
*   **Sanity Metric:** <5% manual override rate on AI-generated monthly rotations.
*   **Audit Certainty:** 100% acceptance of "Export for Audit" reports by the Scientific Council.
*   **Clinical Safety:** knowledge gaps on "Conflict" topics turn from Red to Green on the resident heatmap.

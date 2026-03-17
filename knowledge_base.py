"""
Lightweight framework knowledge base.
Key clauses and artifacts from each framework, organized by domain.
Used for citation in the mapping output — lightweight alternative to full RAG.
"""

FRAMEWORK_CLAUSES = {
    "SABSA": {
        "Identity": [
            {"id": "SABSA-L2-ID", "clause": "Logical Layer — Identity Management Service: defines authentication, authorisation and accounting (AAA) services as core logical security services."},
            {"id": "SABSA-C1-BA", "clause": "Contextual Layer — Business Attribute Profile: maps identity assurance levels to business risk tolerance and regulatory obligations."},
        ],
        "Network": [
            {"id": "SABSA-L3-NS", "clause": "Physical Layer — Network Security Controls: specifies network segmentation, perimeter controls, and inter-zone traffic inspection requirements."},
            {"id": "SABSA-L2-ZS", "clause": "Logical Layer — Zone Security Model: defines security zones and conduits, trust levels, and inter-zone communication policies."},
        ],
        "Data": [
            {"id": "SABSA-L2-IM", "clause": "Logical Layer — Information Management: data classification, labelling, handling, and lifecycle controls derived from the Business Attribute Profile."},
        ],
        "Governance": [
            {"id": "SABSA-C1-RM", "clause": "Contextual Layer — Risk & Opportunity Model: establishes the organisation's risk appetite, threat model, and security governance charter."},
            {"id": "SABSA-O6-SM", "clause": "Operational Layer — Security Service Management: defines security operations processes aligned to business service requirements."},
        ],
        "Cloud Security": [
            {"id": "SABSA-L2-CA", "clause": "Logical Layer — Cloud Security Architecture: extends the logical security services model to cloud-delivered services, covering shared responsibility and multi-tenancy controls."},
        ],
        "Application": [
            {"id": "SABSA-L2-AS", "clause": "Logical Layer — Application Security Services: defines application-level authentication, session management, input validation, and API security controls."},
        ],
    },
    "TOGAF": {
        "Governance": [
            {"id": "TOGAF-PhA", "clause": "Phase A — Architecture Vision: establishes security requirements as first-class architecture drivers, defines security principles and constraints for the ADM cycle."},
            {"id": "TOGAF-PhB", "clause": "Phase B — Business Architecture: identifies business processes dependent on security services; maps security capabilities to business value streams."},
        ],
        "Cloud Security": [
            {"id": "TOGAF-PhE", "clause": "Phase E — Opportunities & Solutions: identifies cloud migration work packages, defines security transition architectures for hybrid environments."},
            {"id": "TOGAF-PhF", "clause": "Phase F — Migration Planning: sequences security controls deployment across migration waves; defines security acceptance criteria for each transition state."},
        ],
        "Application": [
            {"id": "TOGAF-PhC-IS", "clause": "Phase C — Information Systems Architecture: defines application security requirements, API governance standards, and data flow security controls."},
        ],
        "Identity": [
            {"id": "TOGAF-PhC-D", "clause": "Phase C — Data Architecture: establishes identity data governance, directory services architecture, and federated identity standards."},
        ],
    },
    "Zachman": {
        "Governance": [
            {"id": "ZACH-R1-W", "clause": "Row 1 (Planner) + Why column: Executive scope — security motivation, business goals, regulatory obligations, and risk strategy at the enterprise planning level."},
            {"id": "ZACH-R2-W", "clause": "Row 2 (Owner) + Why column: Business governance model — security policies, risk ownership, compliance obligations aligned to business units."},
        ],
        "Identity": [
            {"id": "ZACH-R3-WHO", "clause": "Row 3 (Designer) + Who column: Logical people/organisation model — roles, responsibilities, access rights, and identity lifecycle design."},
            {"id": "ZACH-R4-WHO", "clause": "Row 4 (Builder) + Who column: Physical identity implementation — directory services, IAM platform, provisioning workflows."},
        ],
        "Network": [
            {"id": "ZACH-R3-WHERE", "clause": "Row 3 (Designer) + Where column: Logical network model — security zones, trust boundaries, inter-zone communication design."},
            {"id": "ZACH-R4-WHERE", "clause": "Row 4 (Builder) + Where column: Physical network implementation — firewall rules, VPN configuration, cloud network architecture."},
        ],
        "Data": [
            {"id": "ZACH-R3-WHAT", "clause": "Row 3 (Designer) + What column: Logical data model — data classification schema, information security requirements, data flow design."},
        ],
    },
    "NIST CSF": {
        "Governance": [
            {"id": "NIST-GV.RM", "clause": "GV.RM — Risk Management Strategy: establishes risk tolerance, appetite, and organisational priorities to inform cybersecurity decisions. Subcategories include GV.RM-01 (risk appetite), GV.RM-02 (risk strategy), GV.RM-06 (risk response)."},
            {"id": "NIST-GV.OC", "clause": "GV.OC — Organisational Context: defines the mission, stakeholder expectations, legal/regulatory obligations driving cybersecurity risk management."},
            {"id": "NIST-GV.SC", "clause": "GV.SC — Cybersecurity Supply Chain Risk Management: identifies, establishes, and monitors supply chain cybersecurity risks."},
            {"id": "NIST-ID.RA", "clause": "ID.RA — Risk Assessment: cyber risk to assets, suppliers, and individuals is identified, prioritised, and communicated. Subcategories: ID.RA-01 (vulnerabilities identified), ID.RA-05 (threats and vulnerabilities matched to assets), ID.RA-08 (processes for risk response)."},
        ],
        "Identity": [
            {"id": "NIST-PR.AA", "clause": "PR.AA — Identity Management, Authentication and Access Control: manages identities and credentials for authorised users, services, and hardware assets."},
            {"id": "NIST-ID.AM", "clause": "ID.AM — Asset Management: physical and software assets inventoried; asset priority assigned based on classification, criticality, and business value."},
        ],
        "Data": [
            {"id": "NIST-PR.DS", "clause": "PR.DS — Data Security: data-at-rest and data-in-transit are protected consistent with the organisation's risk strategy and data classification policy."},
        ],
        "Detection & Response": [
            {"id": "NIST-DE.CM", "clause": "DE.CM — Continuous Monitoring: information systems and assets monitored at discrete intervals to identify cybersecurity events and verify controls effectiveness."},
            {"id": "NIST-RS.MA", "clause": "RS.MA — Incident Management: incidents are contained, eradicated, and recovered from in coordination with response plans and stakeholder communication."},
        ],
        "Cloud Security": [
            {"id": "NIST-PR.IR", "clause": "PR.IR — Technology Infrastructure Resilience: security architectures managed with resilience in mind, including cloud infrastructure redundancy and failover."},
        ],
        "Application": [
            {"id": "NIST-PR.PS", "clause": "PR.PS — Platform Security: hardware, software, and services managed consistent with risk strategy; vulnerability management applied to all platforms."},
        ],
    },
    "Zero Trust": {
        "Identity": [
            {"id": "ZT-ID", "clause": "NIST SP 800-207 — Identity Pillar: every access request authenticated and authorised based on all available data points including identity, location, device health, and request context. No implicit trust granted based on network location."},
        ],
        "Network": [
            {"id": "ZT-NW", "clause": "NIST SP 800-207 — Network Pillar: network access segmented and isolated; microsegmentation applied to reduce blast radius. Network location not sufficient for access decisions."},
        ],
        "Data": [
            {"id": "ZT-DATA", "clause": "NIST SP 800-207 — Data Pillar: all data categorised and protected based on sensitivity; data access decisions enforced at the resource level regardless of network location."},
        ],
        "Application": [
            {"id": "ZT-APP", "clause": "NIST SP 800-207 — Application & Workload Pillar: applications accessed securely regardless of hosting location; in-application controls enforce least-privilege access."},
        ],
        "Detection & Response": [
            {"id": "ZT-VA", "clause": "NIST SP 800-207 — Visibility & Analytics Pillar: continuous telemetry collected across all pillars; behavioural analytics applied to detect anomalies and policy violations."},
        ],
        "Cloud Security": [
            {"id": "ZT-AUTO", "clause": "NIST SP 800-207 — Automation & Orchestration Pillar: security responses automated and orchestrated across cloud environments; policy enforcement consistent across hybrid deployments."},
        ],
    },
}

def get_citations(domain: str, frameworks: list) -> list:
    citations = []
    for fw in frameworks:
        if fw in FRAMEWORK_CLAUSES and domain in FRAMEWORK_CLAUSES[fw]:
            clauses = FRAMEWORK_CLAUSES[fw][domain]
            if clauses:
                citations.append({
                    "framework": fw,
                    "id": clauses[0]["id"],
                    "clause": clauses[0]["clause"]
                })
    return citations

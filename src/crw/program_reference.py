"""Illustrative reference configurations for the attribute-review and impact-assessment programs.

Every class, score, weight, tier threshold and rule below is an illustrative assumption for synthetic research.
Evidence entries cite public sources that discuss the risk area; none of them prescribes these values.
"""

from __future__ import annotations

ENTITY_TYPES = (
    "individual",
    "sole_proprietor",
    "private_company",
    "public_company",
    "trust",
    "investment_vehicle",
    "financial_institution_regulated",
    "financial_institution_nonbank",
    "government_entity",
)

_FFIEC = "https://bsaaml.ffiec.gov/manual/RisksAssociatedWithMoneyLaunderingAndTerroristFinancing/"

EVIDENCE = [
    ("FFIEC-CIB", "FFIEC BSA/AML Examination Manual: Cash-Intensive Businesses", "supervisory_guidance", "FFIEC",
     "Overview section; lists common examples and risk factors", _FFIEC + "26"),
    ("FFIEC-NBFI", "FFIEC BSA/AML Examination Manual: Nonbank Financial Institutions", "supervisory_guidance", "FFIEC",
     "Overview section", _FFIEC + "22"),
    ("FFIEC-PEP", "FFIEC BSA/AML Examination Manual: Politically Exposed Persons", "supervisory_guidance", "FFIEC",
     "Overview section; states no customer type automatically presents higher risk", _FFIEC + "20"),
    ("FFIEC-TRUST", "FFIEC BSA/AML Examination Manual: Trust and Asset Management Services", "supervisory_guidance",
     "FFIEC", "Overview section", _FFIEC + "18"),
    ("FFIEC-PSP", "FFIEC BSA/AML Examination Manual: Professional Service Providers", "supervisory_guidance", "FFIEC",
     "Overview section", _FFIEC + "23"),
    ("FFIEC-BE", "FFIEC BSA/AML Examination Manual: Business Entities (Domestic and Foreign)", "supervisory_guidance",
     "FFIEC", "Overview section", _FFIEC + "25"),
    ("CFR-1010-230", "31 CFR 1010.230: Beneficial ownership requirements for legal entity customers", "regulation",
     "FinCEN", "Definitions and exclusions, including listed companies and governmental entities",
     "https://www.ecfr.gov/current/title-31/section-1010.230"),
    ("CFR-1022-380", "31 CFR 1022.380: Registration of money services businesses", "regulation", "FinCEN",
     "Registration requirement", "https://www.ecfr.gov/current/title-31/section-1022.380"),
    ("CFR-1027", "31 CFR Part 1027: Dealers in precious metals, precious stones, or jewels", "regulation", "FinCEN",
     "AML program requirement for covered dealers", "https://www.ecfr.gov/current/title-31/part-1027"),
    ("FATF-RBA-BANK", "FATF Guidance for a Risk-Based Approach: The Banking Sector", "industry_guidance", "FATF",
     "Customer, geographic and product/service risk factors",
     "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Risk-based-approach-banking-sector.html"),
    ("OFAC-PROGRAMS", "OFAC Sanctions Programs and Country Information", "regulation", "U.S. Treasury OFAC",
     "Program index; screening and blocking obligations sit outside risk rating",
     "https://ofac.treasury.gov/sanctions-programs-and-country-information"),
    ("POLICY-ILLUSTRATIVE", "Illustrative adopter policy statement (synthetic placeholder)", "internal_policy",
     "Adopter (placeholder)", "Replace with the adopter's approved policy reference before any use", None),
]


def _a(cls: str, score=None) -> dict:
    return {"class": cls, "score": score}


N, E, M = "neutral", "elevator", "mitigator"


def _value(value_id, label, current, *, proposed=None, evidence=(), rationale="", status="unreviewed"):
    return {
        "id": value_id,
        "label": label,
        "current": current,
        "proposed": proposed,
        "evidence": list(evidence),
        "rationale": rationale,
        "status": status,
    }


def reference_catalog() -> dict:
    v = _value
    attributes = [
        {
            "id": "entity_type",
            "label": "Entity type",
            "category": "customer",
            "definition": "Legal form of the party as resolved by entity segmentation.",
            "applies_to": ["all"],
            "missing": "review",
            "values": [
                v("individual", "Natural person", _a(N, 50)),
                v("sole_proprietor", "Sole proprietor", _a(N, 50)),
                v("private_company", "Private operating company", _a(N, 50)),
                v("public_company", "Publicly traded company", _a(N, 50)),
                v("trust", "Trust", _a(E, 60), evidence=["FFIEC-TRUST"]),
                v("investment_vehicle", "Private investment vehicle", _a(E, 65), evidence=["FFIEC-BE", "CFR-1010-230"]),
                v("financial_institution_regulated", "Regulated financial institution", _a(M, 40),
                  evidence=["POLICY-ILLUSTRATIVE"]),
                v("financial_institution_nonbank", "Nonbank financial institution", _a(E, 70), evidence=["FFIEC-NBFI"]),
                v("government_entity", "Domestic governmental entity", _a("override_low"), evidence=["CFR-1010-230"]),
            ],
        },
        {
            "id": "nature_of_business",
            "label": "Nature of business",
            "category": "customer",
            "definition": "Primary business activity of a non-individual party, normalized to a controlled list.",
            "applies_to": ["sole_proprietor", "private_company", "public_company", "investment_vehicle",
                           "financial_institution_regulated", "financial_institution_nonbank"],
            "missing": "review",
            "values": [
                v("general_retail", "General retail", _a(N, 50)),
                v("manufacturing", "Manufacturing", _a(N, 50)),
                v("professional_services", "Professional services", _a(N, 50)),
                v("legal_accounting_intermediary", "Legal or accounting intermediary", _a(E, 60), evidence=["FFIEC-PSP"]),
                v("restaurant", "Restaurant", _a(E, 60), evidence=["FFIEC-CIB"]),
                v("convenience_store", "Convenience store", _a(E, 70), evidence=["FFIEC-CIB"]),
                v("liquor_store", "Liquor store", _a(E, 70), evidence=["FFIEC-CIB"]),
                v("vending_machine_operator", "Vending machine operator", _a(E, 65), evidence=["FFIEC-CIB"]),
                v("parking_garage", "Parking garage", _a(N, 50), proposed=_a(E, 60), evidence=["FFIEC-CIB"],
                  rationale="Listed among common cash-intensive examples; currently unscored. Proposal aligns it with comparable cash businesses.",
                  status="proposed"),
                v("privately_owned_atm_operator", "Privately owned ATM operator", _a(E, 75),
                  proposed=_a("override_high"), evidence=["FFIEC-CIB", "POLICY-ILLUSTRATIVE"],
                  rationale="Illustrative escalation to a trigger: cash replenishment source is hard to verify. Requires policy-owner agreement.",
                  status="proposed"),
                v("precious_metals_dealer", "Dealer in precious metals, stones or jewels", _a(E, 70), evidence=["CFR-1027"]),
                v("money_services_business", "Registered money services business", _a(E, 70), evidence=["FFIEC-NBFI"]),
                v("unregistered_money_transmission", "Money transmission without required registration",
                  _a("override_high"), evidence=["CFR-1022-380"]),
                v("import_export_trading", "Import and export trading", _a(E, 60), evidence=["FATF-RBA-BANK"]),
                v("online_marketplace_seller", "Online marketplace seller", None),
            ],
        },
        {
            "id": "occupation",
            "label": "Occupation",
            "category": "customer",
            "definition": "Occupation of an individual or sole proprietor, normalized to a controlled list.",
            "applies_to": ["individual", "sole_proprietor"],
            "missing": "neutral",
            "values": [
                v("salaried_employee", "Salaried employee", _a(N, 50)),
                v("retired", "Retired", _a(M, 45), evidence=["POLICY-ILLUSTRATIVE"]),
                v("student", "Student", _a(N, 50)),
                v("not_employed", "Not employed", _a(N, 50)),
                v("self_employed_professional", "Self-employed professional", _a(N, 50)),
                v("cash_based_self_employment", "Cash-based self-employment", _a(E, 60), evidence=["FFIEC-CIB"]),
                v("senior_foreign_public_official", "Senior foreign public official", _a(E, 65), evidence=["FFIEC-PEP"],
                  rationale="Contextual elevator only. The cited section states no customer type automatically presents higher risk."),
            ],
        },
        {
            "id": "listed_status",
            "label": "Listed status",
            "category": "customer",
            "definition": "Whether a legal entity or its parent is listed on a regulated exchange.",
            "applies_to": ["private_company", "public_company", "investment_vehicle",
                           "financial_institution_regulated", "financial_institution_nonbank"],
            "missing": "review",
            "values": [
                v("listed_regulated_exchange", "Listed on a regulated exchange", _a(M, 35), evidence=["CFR-1010-230"]),
                v("subsidiary_of_listed", "Majority-owned subsidiary of a listed company", _a(M, 40), evidence=["CFR-1010-230"]),
                v("unlisted_private", "Unlisted private entity", _a(N, 50)),
                v("unlisted_unregulated_structure", "Unlisted, unregulated holding structure", _a(E, 65), evidence=["FFIEC-BE"]),
            ],
        },
        {
            "id": "source_of_wealth",
            "label": "Source of wealth",
            "category": "funds",
            "definition": "Origin of the party's overall wealth as declared and corroborated at onboarding or refresh.",
            "applies_to": ["all"],
            "missing": "review",
            "values": [
                v("employment_income", "Employment income", _a(N, 50)),
                v("business_ownership", "Business ownership", _a(N, 50)),
                v("inheritance_or_gift", "Inheritance or gift", _a(N, 50)),
                v("investment_returns", "Investment returns", _a(N, 50)),
                v("sale_of_business_or_property", "Sale of business or property", _a(N, 50)),
                v("undocumented", "Undocumented", _a(E, 70), evidence=["FATF-RBA-BANK"]),
            ],
        },
        {
            "id": "source_of_funds",
            "label": "Source of funds",
            "category": "funds",
            "definition": "Origin of the funds used in the relationship.",
            "applies_to": ["all"],
            "missing": "review",
            "values": [
                v("own_account_same_institution", "Own account at the same institution", _a(M, 45),
                  evidence=["POLICY-ILLUSTRATIVE"]),
                v("external_bank_transfer", "Transfer from an external bank account", _a(N, 50)),
                v("payroll", "Payroll", _a(N, 50)),
                v("cash_deposit", "Cash deposit", _a(E, 60), evidence=["FFIEC-CIB"]),
                v("third_party_unrelated", "Unrelated third party", _a(E, 65), evidence=["FATF-RBA-BANK"]),
                v("virtual_asset_service_provider", "Virtual asset service provider", _a(E, 60), proposed=_a(N, 50),
                  evidence=["POLICY-ILLUSTRATIVE"],
                  rationale="Proposed de-escalation when the provider is registered and transfer originator data is available; challenged pending policy evidence.",
                  status="challenged"),
                v("unverified", "Unverified", _a(E, 70), evidence=["FATF-RBA-BANK"]),
            ],
        },
        {
            "id": "jurisdiction_exposure",
            "label": "Jurisdiction exposure",
            "category": "geography",
            "definition": "Highest-risk jurisdiction band connected to residence, incorporation or operations. Band membership is adopter-defined.",
            "applies_to": ["all"],
            "missing": "review",
            "values": [
                v("domestic_only", "Domestic only", _a(N, 50)),
                v("standard_international", "Standard international", _a(N, 50)),
                v("elevated_risk", "Elevated-risk jurisdiction band", _a(E, 70), evidence=["FATF-RBA-BANK"]),
                v("comprehensively_sanctioned", "Comprehensively sanctioned jurisdiction", _a("override_high"),
                  evidence=["OFAC-PROGRAMS"],
                  rationale="Risk-rating consequence only. Screening, blocking and reporting obligations are handled by a separate workflow."),
            ],
        },
        {
            "id": "account_purpose",
            "label": "Account purpose",
            "category": "product",
            "definition": "Declared purpose and intended use of the relationship.",
            "applies_to": ["all"],
            "missing": "neutral",
            "values": [
                v("long_term_investment", "Long-term investment", _a(N, 50)),
                v("operating_or_payroll", "Operating or payroll", _a(N, 50)),
                v("cross_border_payments", "Frequent cross-border payments", _a(E, 60), evidence=["FATF-RBA-BANK"]),
                v("unclear_or_pass_through", "Unclear or pass-through", _a(E, 70), evidence=["FATF-RBA-BANK"]),
            ],
        },
    ]
    for attribute in attributes:
        for value in attribute["values"]:
            if value["status"] == "unreviewed" and value["current"] is not None and value["evidence"]:
                value["status"] = "deferred" if value["current"]["class"] == "override_high" else "unreviewed"
    return {
        "catalog_id": "reference-attribute-catalog",
        "version": "1.0.0",
        "description": "Illustrative categorical attribute catalog for synthetic research. Classes and scores are assumptions, not sourced prescriptions.",
        "scale": {"minimum": 0, "maximum": 100, "neutral": 50},
        "entity_types": list(ENTITY_TYPES),
        "attributes": attributes,
        "evidence": [
            {k: val for k, val in zip(("id", "title", "kind", "issuer", "locator", "url"), e) if val is not None}
            | {"public": True}
            for e in EVIDENCE
        ],
    }


def reference_model() -> dict:
    return {
        "model_id": "reference-categorical-model",
        "version": "1.0.0",
        "description": "Weighted mean of value scores with value overrides and rule floors. Weights and thresholds are illustrative.",
        "weights": {
            "entity_type": 1.0,
            "nature_of_business": 1.5,
            "occupation": 1.0,
            "listed_status": 1.0,
            "source_of_wealth": 1.2,
            "source_of_funds": 1.5,
            "jurisdiction_exposure": 1.5,
            "account_purpose": 1.0,
        },
        "tiers": [
            {"name": "LOW", "minimum": 0},
            {"name": "MODERATE", "minimum": 50.5},
            {"name": "HIGH", "minimum": 54},
            {"name": "VERY_HIGH", "minimum": 58},
        ],
        "missing": "neutral",
        "override_high_tier": "VERY_HIGH",
        "override_low_tier": "LOW",
    }


CASH_BUSINESSES = ["restaurant", "convenience_store", "liquor_store", "vending_machine_operator", "parking_garage",
                   "privately_owned_atm_operator"]


def reference_rules() -> dict:
    return {
        "ruleset_id": "reference-rules",
        "version": "1.0.0",
        "description": "Illustrative atomic and compound rules. Floors set a minimum tier; routes request review without changing the tier.",
        "rules": [
            {
                "id": "ATOM-01",
                "title": "Regulated value-transfer or high-value-goods business",
                "condition": {"attribute": "nature_of_business", "in": ["money_services_business", "precious_metals_dealer"]},
                "effect": {"type": "floor", "tier": "HIGH"},
                "evidence": ["FFIEC-NBFI", "CFR-1027"],
                "rationale": "Business types with dedicated AML program obligations receive at least HIGH regardless of other attributes.",
                "status": "proposed",
            },
            {
                "id": "ATOM-02",
                "title": "Elevated-risk jurisdiction band",
                "condition": {"attribute": "jurisdiction_exposure", "in": ["elevated_risk"]},
                "effect": {"type": "floor", "tier": "HIGH"},
                "evidence": ["FATF-RBA-BANK"],
                "rationale": "Geographic exposure in the adopter's elevated band sets a HIGH minimum.",
                "status": "proposed",
            },
            {
                "id": "COMP-01",
                "title": "Nonbank institution with third-party or unverified funds in an unregulated structure",
                "condition": {"all": [
                    {"attribute": "entity_type", "in": ["financial_institution_nonbank"]},
                    {"attribute": "source_of_funds", "in": ["third_party_unrelated", "unverified"]},
                    {"attribute": "listed_status", "in": ["unlisted_unregulated_structure"]},
                ]},
                "effect": {"type": "floor", "tier": "VERY_HIGH"},
                "evidence": ["FFIEC-NBFI", "FFIEC-BE", "FATF-RBA-BANK"],
                "rationale": "Each leg is an elevator alone; together they leave no independent check on the origin of funds.",
                "status": "proposed",
            },
            {
                "id": "COMP-02",
                "title": "Senior foreign public official with undocumented wealth",
                "condition": {"all": [
                    {"attribute": "occupation", "in": ["senior_foreign_public_official"]},
                    {"attribute": "source_of_wealth", "in": ["undocumented"]},
                ]},
                "effect": {"type": "floor", "tier": "VERY_HIGH"},
                "evidence": ["FFIEC-PEP"],
                "rationale": "Public-function exposure is contextual; combined with undocumented wealth it sets the top tier pending documentation.",
                "status": "proposed",
            },
            {
                "id": "COMP-03",
                "title": "Cash-intensive business funding cross-border payments with cash",
                "condition": {"all": [
                    {"attribute": "nature_of_business", "in": CASH_BUSINESSES},
                    {"attribute": "source_of_funds", "in": ["cash_deposit"]},
                    {"attribute": "account_purpose", "in": ["cross_border_payments"]},
                ]},
                "effect": {"type": "floor", "tier": "HIGH"},
                "evidence": ["FFIEC-CIB", "FATF-RBA-BANK"],
                "rationale": "Draft: support and contribution of each leg to be confirmed in the connections review.",
                "status": "draft",
            },
            {
                "id": "ROUTE-01",
                "title": "Unclear account purpose",
                "condition": {"attribute": "account_purpose", "in": ["unclear_or_pass_through"]},
                "effect": {"type": "route", "action": "Request purpose-of-account clarification; no tier change from this rule."},
                "evidence": ["FATF-RBA-BANK"],
                "rationale": "Missing purpose is an information gap to close before it is a risk conclusion.",
                "status": "proposed",
            },
        ],
    }


def reference_party_roles() -> dict:
    return {
        "config_id": "reference-party-roles",
        "version": "1.0.0",
        "description": "Illustrative role-to-scope mapping. Influence follows the ownership and control concepts of 31 CFR 1010.230.",
        "scope_classes": [
            {"id": "customer", "rated": True, "description": "Holds the relationship in its own name."},
            {"id": "related_with_influence", "rated": True,
             "description": "Can own, control or direct the relationship (for example ownership or control prong, trustee, attorney-in-fact)."},
            {"id": "related_without_influence", "rated": False,
             "description": "Connected but cannot direct the relationship (for example contingent beneficiary, notification party)."},
        ],
        "roles": {
            "account_holder": "customer",
            "joint_account_holder": "customer",
            "beneficial_owner_ownership": "related_with_influence",
            "controlling_person": "related_with_influence",
            "trustee": "related_with_influence",
            "settlor": "related_with_influence",
            "attorney_in_fact": "related_with_influence",
            "authorized_trader": "related_with_influence",
            "contingent_beneficiary": "related_without_influence",
            "transfer_on_death_beneficiary": "related_without_influence",
            "duplicate_statement_recipient": "related_without_influence",
        },
    }


def reference_tier_scale() -> dict:
    return {"scale_id": "reference-four-tier", "tiers": ["LOW", "MODERATE", "HIGH", "VERY_HIGH"],
            "codes": {"LOW": 1, "MODERATE": 2, "HIGH": 3, "VERY_HIGH": 4}}


SEGMENTS = ("SEGMENT_A", "SEGMENT_B", "SEGMENT_C", "SEGMENT_D")
AGGREGATE_SEGMENT = "SEGMENT_E"


def reference_assessment_config(assessment_id: str = "IA-DEMO-001") -> dict:
    segments = {s: {"mode": "paired", "description": f"Synthetic business segment {s[-1]}"} for s in SEGMENTS}
    segments[AGGREGATE_SEGMENT] = {"mode": "aggregate_only",
                                   "description": "Synthetic segment too large to snapshot row by row; aggregates only."}
    return {
        "assessment_id": assessment_id,
        "description": "Synthetic demonstration: apply proposed value classifications from the attribute review.",
        "pre_label": "test environment, before release",
        "post_label": "test environment, after release",
        "exclude_pinned": True,
        "segments": segments,
        "unknown_segments": "error",
    }

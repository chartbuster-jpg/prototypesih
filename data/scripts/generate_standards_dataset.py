"""
Generate 500+ Indian Standards records focused on SP 21 / building materials.
Run: python data/scripts/generate_standards_dataset.py
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "standards" / "standards.json"

# Curated seed standards (real or realistic IS numbers for construction / materials)
SEED = [
    {
        "is_number": "IS 456",
        "part": None,
        "title": "Plain and Reinforced Concrete — Code of Practice",
        "domain": "Construction Materials",
        "tags": ["concrete", "structural", "civil"],
        "normative_references": ["IS 383", "IS 516", "IS 2386"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Covers materials, workmanship, inspection and testing for plain and reinforced concrete used in buildings and structures.",
    },
    {
        "is_number": "IS 383",
        "part": None,
        "title": "Coarse and Fine Aggregate for Concrete — Specification",
        "domain": "Construction Materials",
        "tags": ["aggregate", "sand", "concrete"],
        "normative_references": ["IS 2386", "IS 516"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Requirements for natural and crushed aggregates for concrete including grading, deleterious materials and testing.",
    },
    {
        "is_number": "IS 12269",
        "part": None,
        "title": "53 Grade Ordinary Portland Cement — Specification",
        "domain": "Construction Materials",
        "tags": ["cement", "OPC", "building"],
        "normative_references": ["IS 4031", "IS 4032"],
        "certification": "BIS Product Certification: Mandatory",
        "abstract": "Specifies chemical and physical requirements for 53 grade ordinary Portland cement.",
    },
    {
        "is_number": "IS 1239",
        "part": "Part 1",
        "title": "Steel Tubes, Tubulars and Other Wrought Steel Fittings — Part 1: Steel Tubes",
        "domain": "Construction Materials",
        "tags": ["steel", "pipes", "water supply"],
        "normative_references": ["IS 4759", "IS 7793"],
        "certification": "BIS Product Certification: Mandatory",
        "abstract": "Requirements for welded and seamless steel tubes for structural and general engineering purposes.",
    },
    {
        "is_number": "IS 4759",
        "part": None,
        "title": "Hot-Dip Zinc Coatings on Structural Steel and Other Allied Products — Code of Practice",
        "domain": "Construction Materials",
        "tags": ["galvanizing", "coating", "steel"],
        "normative_references": ["IS 1239"],
        "certification": "BIS Product Certification: Mandatory",
        "abstract": "Covers preparation of surfaces and hot-dip galvanizing for corrosion protection of steel products.",
    },
    {
        "is_number": "IS 7793",
        "part": None,
        "title": "Methods of Sampling and Test for Steel Pipes and Tubes",
        "domain": "Testing Methods",
        "tags": ["testing", "steel", "pipes"],
        "normative_references": ["IS 1239"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Sampling and mechanical tests for steel pipes and tubes including tensile and flattening tests.",
    },
    {
        "is_number": "IS 516",
        "part": None,
        "title": "Method of Test for Strength of Concrete",
        "domain": "Testing Methods",
        "tags": ["testing", "concrete", "NABL"],
        "normative_references": ["IS 456"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Standard methods for making and testing concrete specimens for compressive strength.",
    },
    {
        "is_number": "IS 2386",
        "part": "Part 1",
        "title": "Methods of Test for Aggregates for Concrete — Part 1: Particle Size and Shape",
        "domain": "Testing Methods",
        "tags": ["testing", "aggregate"],
        "normative_references": ["IS 383"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Test methods for sieve analysis and shape tests on aggregates for concrete.",
    },
    {
        "is_number": "IS 800",
        "part": None,
        "title": "General Construction in Steel — Code of Practice",
        "domain": "Construction Materials",
        "tags": ["steel", "structural", "design"],
        "normative_references": ["IS 2062", "IS 875"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Design and construction requirements for steel structures including connections and fabrication.",
    },
    {
        "is_number": "IS 2062",
        "part": None,
        "title": "Hot Rolled Medium and High Tensile Structural Steel — Specification",
        "domain": "Construction Materials",
        "tags": ["steel", "structural"],
        "normative_references": ["IS 1608"],
        "certification": "BIS Product Certification: Mandatory",
        "abstract": "Chemical composition and mechanical properties for structural steel plates, sections and bars.",
    },
    {
        "is_number": "IS 875",
        "part": "Part 1",
        "title": "Code of Practice for Design Loads — Part 1: Dead Loads",
        "domain": "Safety Standards",
        "tags": ["loads", "design", "safety"],
        "normative_references": [],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Dead load values for materials and components used in building design.",
    },
    {
        "is_number": "IS 3370",
        "part": "Part 1",
        "title": "Code of Practice for Concrete Structures for Storage of Liquids — Part 1: General Requirements",
        "domain": "Construction Materials",
        "tags": ["water tank", "concrete", "liquid retaining"],
        "normative_references": ["IS 456", "IS 3370"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Design and construction of reinforced concrete structures for storage of liquids.",
    },
    {
        "is_number": "IS 4985",
        "part": None,
        "title": "Unplasticized PVC Pipes for Potable Water Supplies — Specification",
        "domain": "Construction Materials",
        "tags": ["PVC", "pipes", "water supply"],
        "normative_references": ["IS 4984"],
        "certification": "BIS Product Certification: Mandatory",
        "abstract": "Requirements for uPVC pipes for cold water supply including dimensions and hydrostatic pressure.",
    },
    {
        "is_number": "IS 3025",
        "part": "Part 10",
        "title": "Methods of Sampling and Test for Water and Wastewater — Part 10: Turbidity",
        "domain": "Testing Methods",
        "tags": ["water quality", "testing"],
        "normative_references": [],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Determination of turbidity in water and wastewater samples.",
    },
    {
        "is_number": "IS 732",
        "part": None,
        "title": "Code of Practice for Electrical Wiring Installations",
        "domain": "Installation Standards",
        "tags": ["electrical", "wiring", "installation"],
        "normative_references": ["IS 3043"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Safety requirements for electrical wiring systems in buildings.",
    },
    {
        "is_number": "IS 3043",
        "part": None,
        "title": "Code of Practice for Earthing",
        "domain": "Safety Standards",
        "tags": ["earthing", "electrical", "safety"],
        "normative_references": ["IS 732"],
        "certification": "BIS Product Certification: Voluntary",
        "abstract": "Earthing arrangements for electrical installations to ensure safety.",
    },
    {
        "is_number": "IS 13252",
        "part": "Part 1",
        "title": "Information Technology Equipment — Safety — Part 1: General Requirements",
        "domain": "Electronics",
        "tags": ["IT", "safety", "CRS"],
        "normative_references": [],
        "certification": "CRS: Applicable",
        "abstract": "Safety requirements for IT equipment; relevant for compulsory registration scheme compliance.",
    },
    {
        "is_number": "IS 1417",
        "part": None,
        "title": "General Requirements for Hallmarking of Gold and Gold Alloys",
        "domain": "Precious Metals",
        "tags": ["gold", "hallmarking"],
        "normative_references": [],
        "certification": "Hallmarking: Mandatory",
        "abstract": "Purity and marking requirements for gold articles under BIS hallmarking scheme.",
    },
]

DOMAINS = [
    "Construction Materials",
    "Testing Methods",
    "Safety Standards",
    "Installation Standards",
    "Electronics",
    "Chemicals",
    "Precious Metals",
]

PRODUCT_TEMPLATES = [
    ("IS {n}", "Portland Cement — Grade {g}", "Construction Materials", ["cement", "building"]),
    ("IS {n}", "Ready-Mixed Concrete — Specification", "Construction Materials", ["concrete", "RMC"]),
    ("IS {n}", "Structural Steel — Hollow Sections", "Construction Materials", ["steel", "HSS"]),
    ("IS {n}", "Clay Bricks — Classification", "Construction Materials", ["brick", "masonry"]),
    ("IS {n}", "Fly Ash for Use as Pozzolana — Specification", "Construction Materials", ["fly ash", "pozzolana"]),
    ("IS {n}", "Waterproofing Membrane — Specification", "Construction Materials", ["waterproofing", "membrane"]),
    ("IS {n}", "Aluminium Windows — Specification", "Construction Materials", ["aluminium", "windows"]),
    ("IS {n}", "Glass for Building — Safety Requirements", "Safety Standards", ["glass", "safety"]),
    ("IS {n}", "Fire Resistance Test for Building Elements", "Testing Methods", ["fire", "testing"]),
    ("IS {n}", "Acoustic Insulation Materials — Test Methods", "Testing Methods", ["acoustic", "testing"]),
    ("IS {n}", "Scaffolding — Safety Code of Practice", "Safety Standards", ["scaffolding", "construction safety"]),
    ("IS {n}", "Laying of Concrete Pipes — Code of Practice", "Installation Standards", ["pipes", "installation"]),
    ("IS {n}", "Roofing Tiles — Specification", "Construction Materials", ["roofing", "tiles"]),
    ("IS {n}", "Bitumen for Road Works — Specification", "Construction Materials", ["bitumen", "road"]),
    ("IS {n}", "Geotextiles — Specification", "Construction Materials", ["geotextile", "civil"]),
]

MANDATORY_PREFIXES = {"12269", "1239", "4759", "2062", "4985", "4984", "1079", "651"}


def random_date(start_year: int = 2015, end_year: int = 2026) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 9, 1)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()


def make_record(
    is_number: str,
    part: str | None,
    title: str,
    domain: str,
    tags: list[str],
    normative_references: list[str],
    certification: str,
    abstract: str,
    publication_date: str,
    superseded_by: str | None = None,
    amendments: list[str] | None = None,
) -> dict:
    return {
        "is_number": is_number,
        "part": part,
        "title": title,
        "domain": domain,
        "publication_date": publication_date,
        "amendment_history": amendments or [],
        "superseded_by": superseded_by,
        "normative_references": normative_references,
        "certification": certification,
        "abstract": abstract,
        "tags": tags,
        "pdf_url": None,
    }


def expand_dataset(target: int = 520) -> list[dict]:
    records: list[dict] = []
    used_keys: set[str] = set()

    for s in SEED:
        pub = random_date(2018, 2025)
        amends = []
        if random.random() > 0.5:
            amends.append(f"Amendment 1 ({random_date(2024, 2026)[:7]})")
        key = f"{s['is_number']}|{s.get('part')}"
        used_keys.add(key)
        records.append(
            make_record(
                s["is_number"],
                s.get("part"),
                s["title"],
                s["domain"],
                s["tags"],
                s["normative_references"],
                s["certification"],
                s["abstract"],
                pub,
                amendments=amends,
            )
        )

    n = 2000
    while len(records) < target:
        tpl = random.choice(PRODUCT_TEMPLATES)
        num = str(n)
        n += 1
        is_number = tpl[0].format(n=num, g=random.choice(["43", "53", "33"]))
        part = random.choice([None, "Part 1", "Part 2", "Part 3"])
        key = f"{is_number}|{part}"
        if key in used_keys:
            continue
        used_keys.add(key)

        domain = tpl[2]
        tags = tpl[3]
        title = tpl[1]
        if part:
            title = f"{title} — {part}"

        refs = random.sample(
            [r["is_number"] for r in SEED] + [f"IS {random.randint(100, 9999)}"],
            k=random.randint(0, 3),
        )

        cert = "BIS Product Certification: Voluntary"
        if num in MANDATORY_PREFIXES or domain == "Electronics":
            cert = "BIS Product Certification: Mandatory" if domain != "Electronics" else "CRS: Applicable"
        if domain == "Precious Metals":
            cert = "Hallmarking: Mandatory"

        pub = random_date()
        superseded = None
        if random.random() < 0.08:
            superseded = f"{is_number} ({part or 'Rev'}) — {random_date(2024, 2026)[:4]}"

        records.append(
            make_record(
                is_number,
                part,
                title,
                domain,
                tags,
                refs,
                cert,
                f"Specifies requirements for {title.lower()} used in government procurement and public works.",
                pub,
                superseded_by=superseded,
                amendments=[f"Amendment 1 ({random_date(2025, 2026)[:7]})"] if random.random() < 0.3 else [],
            )
        )

    # Version chains: duplicate base numbers with newer publication for get_latest_version
    for base in ["IS 456", "IS 1239", "IS 383", "IS 800"]:
        older = next(r for r in records if r["is_number"] == base and r["part"] in (None, "Part 1"))
        newer_pub = random_date(2024, 2026)
        newer = {**older, "publication_date": newer_pub, "amendment_history": ["Amendment 1 (2025-06)"]}
        older["superseded_by"] = f"{base} — {newer_pub[:4]}"
        records.append(newer)

    return records[: target + 10]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = expand_dataset(520)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(data)} standards to {OUT}")


if __name__ == "__main__":
    main()

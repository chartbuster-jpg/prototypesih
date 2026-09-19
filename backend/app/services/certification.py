from backend.app.config import settings
from backend.app.models.standard import StandardModel
from backend.app.schemas.standard import CertificationInfo

BIS_MANDATORY_KEYWORDS = ("Mandatory", "mandatory")


def get_certification_info(standard: StandardModel) -> CertificationInfo:
    cert_text = standard.certification or ""
    if "CRS" in cert_text:
        bis = "Voluntary (product); CRS registration required"
        crs = True
    elif any(k in cert_text for k in BIS_MANDATORY_KEYWORDS):
        bis = "Mandatory"
        crs = False
    else:
        bis = "Voluntary"
        crs = standard.domain in ("Electronics", "Chemicals")

    hallmarking = standard.domain == "Precious Metals" or "Hallmarking" in cert_text

    return CertificationInfo(
        bis_certification=bis,
        crs_applicable=crs or standard.domain in ("Electronics", "Chemicals"),
        hallmarking=hallmarking,
        fmcs_note="Foreign manufacturers may require FMCS under BIS conformity assessment.",
        certification_portal_link=settings.bis_certification_portal,
    )

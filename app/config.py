import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "sanctions.db"))

SOURCES = {
    "EU": {
        "label": "UE",
        "name": "EU Consolidated Financial Sanctions List",
        "url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
        "info_url": "https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions",
    },
    "UN": {
        "label": "ONZ",
        "name": "UN Security Council Consolidated List",
        "url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
        "info_url": "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list",
    },
    "OFAC": {
        "label": "OFAC",
        "name": "OFAC Specially Designated Nationals (SDN) List",
        "url": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML",
        "info_url": "https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists",
    },
}

# Score thresholds (0-100)
MATCH_THRESHOLD = 90
REVIEW_THRESHOLD = 75
WEAK_THRESHOLD = 60

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
SITE = ROOT / "site"
WEB = ROOT / "web"
FIGURES = ROOT / "reports" / "figures"

BASE = "http://sistemas.midagri.gob.pe/sisap/portal2/mayorista/"   # HTTPS certificate is expired
MARKET = "15011501"                        # Gran Mercado Mayorista de Lima
START = "2010-01-01"
CHUNK_MONTHS = 6                           # the portal rejects ranges of a year ("too many criteria")
SLEEP = 1.0                                # seconds between requests, to be polite with a public server
UPDATE_DAYS = 60                           # re-download window in daily updates (captures revisions)
PAGES_URL = "https://rodgrandez.github.io/lima-food-prices-pipeline/"

CATEGORIES = {"01": "Tubers", "02": "Vegetables", "03": "Fresh legumes", "04": "Cereals", "05": "Dry legumes",
              "06": "Fruits", "09": "Agro-industrial", "10": "Processed", "11": "Dairy"}

OUTLIER_WINDOW = 15                        # previous observations used for the median
OUTLIER_LOG_MAX = 0.7                      # |log(price / median)| above this is a glitch (~2x)
STALE_DAYS = 30                            # identical price for this many observations = stale
DISCONTINUED_DAYS = 30                     # no observation in the last N days = discontinued

SMOOTH_DAYS = 7
CHANGE_DAYS = 28
SHOCK_WEEKS = 26
DIFFUSION_THRESHOLD = 10.0                 # % change over CHANGE_DAYS counted as a rise or a fall

import base64
import csv
import hashlib
import html
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
ENVoy_MARKERS = [
    'window["__envoy_product-info__PROPS"]',
    "window['__envoy_product-info__PROPS']",
    "__envoy_product-info__PROPS",
]
TRENDYOL_BASE = "https://www.trendyol.com"
TRENDYOL_SEARCH_API_URL = "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr"
TRENDYOL_WATCH_CATEGORY_URL = "https://www.trendyol.com/saat-x-c34"
NEKADARSATTI_API_URL = "https://nekadarsatti.com/api/sales-number"
NEKADARSATTI_PUBLIC_API_KEY = "aJ9cgcACBCY1d3dWmJhWW8n2v2GhgP"
NEKADARSATTI_QUERY_LIMIT = 30
AUTH_QUERY_PARAM = "kozade_auth"

LISTING_SORT_OPTIONS = {
    "En çok satan": "BEST_SELLER",
    "En çok ziyaret edilen": "MOST_VISITED",
    "En çok değerlendirilen": "MOST_RATED",
    "En çok favorilenen": "MOST_FAVOURITE",
}
COMMISSION_PRESETS = {
    "Manuel": None,
    "Cep telefonu": 7.0,
    "Laptop / tablet": 8.0,
    "Beyaz eşya": 11.0,
    "Küçük ev aletleri": 15.0,
    "Gıda / süpermarket": 15.25,
    "Anne & bebek": 16.5,
    "Kozmetik / kişisel bakım": 16.78,
    "Mutfak gereçleri / züccaciye": 19.32,
    "Ev tekstili": 20.34,
    "Giyim": 21.36,
    "Çanta": 21.36,
    "Saat": 21.36,
    "Takı / bijuteri": 22.37,
    "Ayakkabı": 23.39,
}
TRENDYOL_PLATFORM_SERVICE_FEE = 13.19
TRENDYOL_SAME_DAY_SERVICE_FEE = 8.39
TRENDYOL_STOPAJ_RATE = 1.0
SAAT_VE_SAAT_BRANDS = [
    "Adidas Originals",
    "Armani Exchange",
    "Boss",
    "Calvin Klein",
    "Cerruti 1881",
    "Diesel",
    "DKNY",
    "Ebel",
    "Emporio Armani",
    "Escape",
    "Esprit",
    "Ferragamo",
    "Fitwatch",
    "Fossil",
    "Furla",
    "Garmin",
    "Gc",
    "Guess",
    "Huawei",
    "Hugo",
    "Jacques Philippe",
    "Kenneth Cole",
    "Lacoste",
    "Laiza",
    "Maurice Lacroix",
    "Mazzucato",
    "Michael Kors",
    "Missoni",
    "Oris",
    "Parigi",
    "Philipp Plein",
    "Police",
    "Puma",
    "Raymond Weil",
    "Roche Montre",
    "Seiko",
    "Seiko 5",
    "Skagen",
    "Skechers",
    "Swarovski",
    "TCL",
    "Ted Baker",
    "Timex",
    "Tommy Hilfiger",
    "Tory Burch",
    "U.S. Polo Assn.",
    "Universe Constant",
    "Versace",
    "Welder",
    "Wesse",
    "Xonix",
]
TRENDYOL_HIGH_VOLUME_BRANDS = [
    "Adidas",
    "Adidas Originals",
    "Altınyıldız Classics",
    "Apple",
    "Arçelik",
    "Armani Exchange",
    "Arzum",
    "Avon",
    "Baby Turco",
    "Bambum",
    "Bargello",
    "Bershka",
    "Bioderma",
    "Bioxcin",
    "Birkenstock",
    "Bosch",
    "Braun",
    "Burberry",
    "Calvin Klein",
    "Casio",
    "Chakra",
    "Chicco",
    "Colin's",
    "Columbia",
    "Converse",
    "Cotton Box",
    "Cream Co.",
    "Crocs",
    "D'S Damat",
    "Daikin",
    "Defacto",
    "Delta",
    "Derimod",
    "Diadermine",
    "Dilvin",
    "Dyson",
    "Emsan",
    "English Home",
    "Estee Lauder",
    "Fakir",
    "Farmasi",
    "Fisher Price",
    "Flormar",
    "Flo",
    "Fossil",
    "Franke",
    "Garnier",
    "Gillette",
    "GoldMaster",
    "Gratis",
    "Guess",
    "H&M",
    "HP",
    "Harley Davidson",
    "Huawei",
    "Hummel",
    "IKEA",
    "Jack & Jones",
    "JBL",
    "KIKO",
    "Karaca",
    "Karaca Home",
    "Karcher",
    "Kiğılı",
    "Kinetix",
    "Koton",
    "Korkmaz",
    "L'Oreal Paris",
    "LC Waikiki",
    "LEGO",
    "La Roche Posay",
    "Lacoste",
    "Lenovo",
    "Levi's",
    "Linens",
    "Logitech",
    "Lumberjack",
    "Mango",
    "Madame Coco",
    "Mavi",
    "Maybelline New York",
    "Monster",
    "Nike",
    "New Balance",
    "New Well",
    "Nine West",
    "Nivea",
    "Oppo",
    "Oral-B",
    "Oriflame",
    "Oxxo",
    "Özdilek",
    "Penti",
    "Pastel",
    "Paşabahçe",
    "Philips",
    "Pierre Cardin",
    "Polo Garage",
    "Porland",
    "Pull&Bear",
    "Puma",
    "Reebok",
    "Roborock",
    "Rossmann",
    "Samsung",
    "Schafer",
    "Skechers",
    "Slazenger",
    "Stradivarius",
    "Suwen",
    "TCL",
    "Taç",
    "Tefal",
    "The North Face",
    "The Purest Solutions",
    "Tommy Hilfiger",
    "Tupperware",
    "U.S. Polo Assn.",
    "Under Armour",
    "Vakko",
    "Vans",
    "Vestel",
    "Victoria's Secret",
    "Watsons",
    "Xiaomi",
    "Yataş",
    "Yves Rocher",
    "Zara",
    "Zara Home",
    "ACAR",
    "AbiyeSultan",
    "Acer",
    "Aclind",
    "Adil Işık",
    "Aker",
    "Alcatel",
    "Alix Avien",
    "Altus",
    "Anker",
    "Arnica",
    "Asus",
    "Atasay",
    "Avva",
    "Bambi",
    "Beko",
    "Beymen",
    "Beymen Club",
    "Bioder",
    "Bissell",
    "Black+Decker",
    "Blue House",
    "Beko",
    "Bonna",
    "Bosch Home",
    "Boyner",
    "Bridgestone",
    "Buratti",
    "Canon",
    "Celenes",
    "Chima",
    "Clinique",
    "Coca-Cola",
    "Cottonhill",
    "Dagi",
    "Damla",
    "Darphin",
    "Decathlon",
    "Dell",
    "Diadora",
    "Dior",
    "Dove",
    "Dr. Oetker",
    "E.C.A.",
    "Eda Taşpınar",
    "Elidor",
    "Elle",
    "Epson",
    "Estee Lauder",
    "Falcon",
    "Fantom",
    "Fitbit",
    "Fox Shoes",
    "General Mobile",
    "George Hogg",
    "Gizia",
    "Goorin Bros",
    "Güral Porselen",
    "Hotiç",
    "Homend",
    "Hometech",
    "Honor",
    "In Street",
    "Inci",
    "İpekyol",
    "Jumbo",
    "Kahve Dünyası",
    "Koton Kids",
    "Kütahya Porselen",
    "Lansinoh",
    "Lee Cooper",
    "Les Benjamins",
    "Madmext",
]
BRAND_STOCK_BRANDS = {
    **{brand: None for brand in TRENDYOL_HIGH_VOLUME_BRANDS},
    **{brand: None for brand in SAAT_VE_SAAT_BRANDS},
    "Apple": "https://www.trendyol.com/apple-x-b101470",
    "Samsung": "https://www.trendyol.com/samsung-x-b794",
    "Xiaomi": "https://www.trendyol.com/xiaomi-x-b101939",
    "Arzum": "https://www.trendyol.com/arzum-x-b392",
    "Dyson": "https://www.trendyol.com/dyson-x-b102989",
    "Fakir": "https://www.trendyol.com/fakir-x-b387",
    "GoldMaster": "https://www.trendyol.com/goldmaster-x-b802",
    "Philips": "https://www.trendyol.com/philips-x-b577",
    "Tefal": "https://www.trendyol.com/tefal-x-b326",
    "Braun": "https://www.trendyol.com/braun-x-b633",
    "Vestel": "https://www.trendyol.com/vestel-x-b102900",
    "Nike": "https://www.trendyol.com/nike-x-b44",
    "Adidas": "https://www.trendyol.com/adidas-x-b33",
    "Puma": "https://www.trendyol.com/puma-x-b160",
    "New Balance": "https://www.trendyol.com/new-balance-x-b128",
    "LEGO": "https://www.trendyol.com/lego-x-b104725",
    "KIKO": "https://www.trendyol.com/kiko-x-b108309",
    "Guess": "https://www.trendyol.com/guess-x-b333",
    "Cream Co.": "https://www.trendyol.com/cream-co-x-b146033",
    "New Well": "https://www.trendyol.com/new-well-x-b104624",
    "The Purest Solutions": "https://www.trendyol.com/the-purest-solutions-x-b132527",
    "Flormar": "https://www.trendyol.com/flormar-x-b988",
    "Pastel": "https://www.trendyol.com/pastel-x-b624",
    "Maybelline New York": "https://www.trendyol.com/maybelline-new-york-x-b476",
    "L'Oreal Paris": "https://www.trendyol.com/l-oreal-paris-x-b568",
    "Mango": "https://www.trendyol.com/mango-x-b41",
    "Zara": "https://www.trendyol.com/zara-x-b40",
    "LC Waikiki": "https://www.trendyol.com/lc-waikiki-x-b859",
    "Madame Coco": "https://www.trendyol.com/madame-coco-x-b52",
    "English Home": "https://www.trendyol.com/english-home-x-b108306",
    "Korkmaz": "https://www.trendyol.com/korkmaz-x-b351",
    "Karaca": "https://www.trendyol.com/karaca-x-b325",
    "Özdilek": "https://www.trendyol.com/ozdilek-x-b283",
    "Taç": "https://www.trendyol.com/tac-x-b261",
    "Karaca Home": "https://www.trendyol.com/karaca-home-x-b653",
    "Yataş": "https://www.trendyol.com/yatas-x-b397",
    "Cotton Box": "https://www.trendyol.com/cotton-box-x-b698",
    "Linens": "https://www.trendyol.com/linens-x-b477",
    "Porland": "https://www.trendyol.com/porland-x-b404",
    "Emsan": "https://www.trendyol.com/emsan-x-b651",
    "Paşabahçe": "https://www.trendyol.com/pasabahce-x-b440",
    "Schafer": "https://www.trendyol.com/schafer-x-b373",
    "Bambum": "https://www.trendyol.com/bambum-x-b776",
    "ACAR": "https://www.trendyol.com/acar-x-b110584",
}
BRAND_STOCK_PRODUCTS_PER_PAGE = 24
LOGO_PATH = Path(__file__).parent / "assets" / "kozade.png"


TRENDYOL_CATEGORIES = {
    "Kadın": "https://www.trendyol.com/kadin-x-g1-c1",
    "Kadın Giyim": "https://www.trendyol.com/kadin-giyim-x-g1-c82",
    "Kadın Ayakkabı": "https://www.trendyol.com/kadin-ayakkabi-x-g1-c114",
    "Kadın Çanta": "https://www.trendyol.com/kadin-canta-x-g1-c117",
    "Erkek": "https://www.trendyol.com/erkek-x-g2-c2",
    "Erkek Giyim": "https://www.trendyol.com/erkek-giyim-x-g2-c82",
    "Erkek Ayakkabı": "https://www.trendyol.com/erkek-ayakkabi-x-g2-c114",
    "Erkek Çanta": "https://www.trendyol.com/erkek-canta-x-g2-c117",
    "Anne & Çocuk": "https://www.trendyol.com/anne-cocuk-x-g3-c103",
    "Bebek": "https://www.trendyol.com/bebek-x-c103442",
    "Çocuk Giyim": "https://www.trendyol.com/cocuk-giyim-x-c103445",
    "Ev & Mobilya": "https://www.trendyol.com/ev-mobilya-x-c104",
    "Ev Tekstili": "https://www.trendyol.com/ev-tekstili-x-c94",
    "Mutfak": "https://www.trendyol.com/mutfak-x-c103757",
    "Mobilya": "https://www.trendyol.com/mobilya-x-c1119",
    "Süpermarket": "https://www.trendyol.com/supermarket-x-c103799",
    "Gıda & İçecek": "https://www.trendyol.com/gida-icecek-x-c103946",
    "Kişisel Bakım": "https://www.trendyol.com/kisisel-bakim-x-c101",
    "Kozmetik": "https://www.trendyol.com/kozmetik-x-c89",
    "Parfüm": "https://www.trendyol.com/parfum-x-c86",
    "Makyaj": "https://www.trendyol.com/makyaj-x-c100",
    "Ayakkabı & Çanta": "https://www.trendyol.com/ayakkabi-canta-x-c114",
    "Elektronik": "https://www.trendyol.com/elektronik-x-c104024",
    "Telefon": "https://www.trendyol.com/cep-telefonu-x-c103498",
    "Bilgisayar & Tablet": "https://www.trendyol.com/bilgisayar-tablet-x-c103665",
    "Küçük Ev Aletleri": "https://www.trendyol.com/kucuk-ev-aletleri-x-c1079",
    "Spor & Outdoor": "https://www.trendyol.com/spor-outdoor-x-c104593",
    "Spor Giyim": "https://www.trendyol.com/spor-giyim-x-c101447",
    "Spor Ayakkabı": "https://www.trendyol.com/spor-ayakkabi-x-c109",
    "Saat & Aksesuar": "https://www.trendyol.com/saat-aksesuar-x-c124",
    "Saat": "https://www.trendyol.com/saat-x-c34",
    "Gözlük": "https://www.trendyol.com/gozluk-x-c105",
    "Takı & Mücevher": "https://www.trendyol.com/taki-mucevher-x-c28",
    "Oyuncak": "https://www.trendyol.com/oyuncak-x-c90",
    "Kitap": "https://www.trendyol.com/kitap-x-c91",
    "Hobi & Kırtasiye": "https://www.trendyol.com/hobi-kirtasiye-x-c103",
    "Otomobil & Motosiklet": "https://www.trendyol.com/otomobil-motosiklet-x-c103483",
    "Yapı Market": "https://www.trendyol.com/yapi-market-x-c103720",
    "Pet Shop": "https://www.trendyol.com/pet-shop-x-c1142"
}


CATEGORY_BRANDS = {
    "Saat & Aksesuar": ["Guess", "Casio", "Ferrucci", "Daniel Klein", "Slazenger", "Q&Q", "Polo Air", "Michael Kors"],
    "Saat": ["Guess", "Casio", "Ferrucci", "Daniel Klein", "Slazenger", "Q&Q", "Polo Air", "Michael Kors"],
    "Gözlük": ["Ray-Ban", "Osse", "Hawk", "Tom Ford", "Guess", "Vogue", "Police"],
    "Kozmetik": ["Maybelline", "L'Oreal Paris", "Flormar", "Pastel", "NYX", "Revolution", "The Purest Solutions"],
    "Parfüm": ["Avon", "Farmasi", "Bargello", "David Walker", "Calvin Klein", "Hugo Boss"],
    "Makyaj": ["Maybelline", "L'Oreal Paris", "Flormar", "Pastel", "NYX", "Revolution"],
    "Elektronik": ["Apple", "Samsung", "Xiaomi", "Huawei", "Philips", "Tefal", "Arzum", "Fakir"],
    "Telefon": ["Apple", "Samsung", "Xiaomi", "Huawei", "Oppo", "Realme", "Tecno"],
    "Bilgisayar & Tablet": ["Apple", "Lenovo", "HP", "Asus", "Acer", "Samsung", "Huawei"],
    "Küçük Ev Aletleri": ["Philips", "Tefal", "Arzum", "Fakir", "Karaca", "Korkmaz", "Grundig"],
    "Ayakkabı & Çanta": ["Nike", "Adidas", "Puma", "Skechers", "Lumberjack", "Derimod", "Pierre Cardin"],
    "Kadın Ayakkabı": ["Nike", "Adidas", "Puma", "Skechers", "Lumberjack", "Derimod", "İnci"],
    "Erkek Ayakkabı": ["Nike", "Adidas", "Puma", "Skechers", "Lumberjack", "Greyder"],
    "Spor & Outdoor": ["Nike", "Adidas", "Puma", "Under Armour", "Skechers", "Lescon", "Decathlon"],
    "Spor Giyim": ["Nike", "Adidas", "Puma", "Under Armour", "Lescon", "Hummel"],
    "Spor Ayakkabı": ["Nike", "Adidas", "Puma", "Skechers", "New Balance", "Asics"],
    "Kadın": ["TrendyolMilla", "Defacto", "LC Waikiki", "Koton", "Mango", "Zara", "Dilvin"],
    "Kadın Giyim": ["TrendyolMilla", "Defacto", "LC Waikiki", "Koton", "Mango", "Zara", "Dilvin"],
    "Erkek": ["Defacto", "LC Waikiki", "Koton", "Mavi", "Jack & Jones", "Avva", "Kiğılı"],
    "Erkek Giyim": ["Defacto", "LC Waikiki", "Koton", "Mavi", "Jack & Jones", "Avva", "Kiğılı"],
    "Ev & Mobilya": ["Karaca", "Korkmaz", "Madame Coco", "English Home", "Taç", "Schafer"],
    "Ev Tekstili": ["Madame Coco", "English Home", "Taç", "Özdilek", "Karaca Home"],
    "Mutfak": ["Karaca", "Korkmaz", "Schafer", "Emsan", "Paşabahçe", "Tefal"],
}


st.set_page_config(
    page_title="Trendyol Fırsat Radarı",
    page_icon=None,
    layout="wide",
)


def require_password():
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        return True

    auth_token = hashlib.sha256(app_password.encode("utf-8")).hexdigest()
    query_token = st.query_params.get(AUTH_QUERY_PARAM)
    if query_token == auth_token:
        st.session_state["authenticated"] = True
        return True

    if st.session_state.get("authenticated"):
        if st.query_params.get(AUTH_QUERY_PARAM) != auth_token:
            st.query_params[AUTH_QUERY_PARAM] = auth_token
        return True

    st.title("Trendyol Fırsat Radarı")
    st.caption("Devam etmek için giriş yap.")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş yap", type="primary"):
        if password == app_password:
            st.session_state["authenticated"] = True
            st.query_params[AUTH_QUERY_PARAM] = auth_token
            st.rerun()
        else:
            st.error("Şifre hatalı.")
    return False


if not require_password():
    st.stop()


def image_data_uri(path):
    if not path.exists():
        return None

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def apply_kozade_theme():
    logo_uri = image_data_uri(LOGO_PATH)
    logo_markup = f'<img class="kozade-logo" src="{logo_uri}" alt="kozade">' if logo_uri else ""
    palette = {
        "cream": "#e5dfd2",
        "cream_2": "#d9d1c2",
        "ink": "#050505",
        "muted": "#70695d",
        "line": "#cfc5b5",
        "card": "#f5f0e6",
        "button_bg": "#050505",
        "button_text": "#e5dfd2",
        "button_hover": "#26231f",
        "status_bg": "rgba(245, 240, 230, 0.74)",
    }
    st.markdown(
        f"""
        <style>
        :root {{
            --kozade-cream: {palette["cream"]};
            --kozade-cream-2: {palette["cream_2"]};
            --kozade-ink: {palette["ink"]};
            --kozade-muted: {palette["muted"]};
            --kozade-line: {palette["line"]};
            --kozade-card: {palette["card"]};
            --kozade-button-bg: {palette["button_bg"]};
            --kozade-button-text: {palette["button_text"]};
            --kozade-button-hover: {palette["button_hover"]};
            --kozade-status-bg: {palette["status_bg"]};
        }}

        .stApp {{
            background: var(--kozade-cream);
            color: var(--kozade-ink);
        }}

        .block-container {{
            padding-top: 5.25rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1480px;
        }}

        .kozade-logo {{
            position: absolute;
            top: 1.15rem;
            right: 2rem;
            width: 142px;
            height: auto;
            z-index: 999999;
            mix-blend-mode: multiply;
        }}

        h1, h2, h3, h4, h5, h6,
        p, label, span, div {{
            color: var(--kozade-ink);
        }}

        h1 {{
            letter-spacing: 0;
            font-weight: 800;
        }}

        .stCaption, [data-testid="stCaptionContainer"], .stMarkdown p {{
            color: var(--kozade-muted);
        }}

        [data-testid="stTabs"] [role="tablist"] {{
            border-bottom: 1px solid var(--kozade-line);
            gap: 0.25rem;
        }}

        [data-testid="stTabs"] [role="tab"] {{
            color: var(--kozade-muted);
            background: transparent;
            border-radius: 0;
            padding: 0.75rem 1rem;
        }}

        [data-testid="stTabs"] [aria-selected="true"] {{
            color: var(--kozade-ink);
            border-bottom: 3px solid var(--kozade-ink);
            font-weight: 800;
        }}

        .stButton > button,
        .stDownloadButton > button {{
            background: var(--kozade-button-bg);
            color: var(--kozade-button-text) !important;
            border: 1px solid var(--kozade-button-bg);
            border-radius: 6px;
            font-weight: 800;
        }}

        .stButton > button *,
        .stButton > button p,
        .stButton > button span,
        .stButton > button div,
        .stDownloadButton > button *,
        .stDownloadButton > button p,
        .stDownloadButton > button span,
        .stDownloadButton > button div,
        [data-testid="stNumberInput"] button *,
        [data-testid="stNumberInput"] button svg {{
            color: var(--kozade-button-text) !important;
            fill: var(--kozade-button-text) !important;
        }}

        [data-testid="stNumberInput"] button {{
            background: var(--kozade-button-bg) !important;
            border-color: var(--kozade-button-bg) !important;
            color: var(--kozade-button-text) !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover {{
            background: var(--kozade-button-hover);
            color: var(--kozade-button-text) !important;
            border-color: var(--kozade-button-hover);
        }}

        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div,
        [data-testid="stNumberInput"] input,
        textarea {{
            background: var(--kozade-card);
            color: var(--kozade-ink) !important;
            border-color: var(--kozade-line);
            border-radius: 6px;
        }}

        [data-baseweb="input"] input,
        [data-baseweb="input"] span,
        [data-baseweb="select"] span,
        [data-baseweb="select"] input,
        [data-baseweb="textarea"] textarea,
        [data-testid="stNumberInput"] input {{
            color: var(--kozade-ink) !important;
            caret-color: var(--kozade-ink) !important;
        }}

        [data-baseweb="input"] input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder {{
            color: var(--kozade-muted) !important;
            opacity: 1;
        }}

        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] ul {{
            background: var(--kozade-ink);
            border: 1px solid var(--kozade-line);
        }}

        [data-baseweb="popover"] [role="option"],
        [data-baseweb="popover"] li,
        [data-baseweb="popover"] div {{
            color: var(--kozade-cream) !important;
        }}

        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="popover"] li:hover {{
            background: #2a2824 !important;
            color: var(--kozade-cream) !important;
        }}

        [data-baseweb="tooltip"],
        [data-baseweb="tooltip"] *,
        [data-testid="stTooltipContent"],
        [data-testid="stTooltipContent"] * {{
            background: var(--kozade-ink) !important;
            color: var(--kozade-cream) !important;
            fill: var(--kozade-cream) !important;
        }}

        [data-baseweb="tag"] {{
            background: #f35f55;
            color: var(--kozade-ink);
        }}

        [data-baseweb="tag"] span {{
            color: var(--kozade-ink) !important;
            font-weight: 800;
        }}

        [data-testid="stExpander"],
        [data-testid="stStatusWidget"] {{
            background: var(--kozade-status-bg);
            border: 1px solid var(--kozade-line);
            border-radius: 8px;
        }}

        [data-testid="stStatusWidget"] > div:first-child,
        [data-testid="stStatusWidget"] > div:first-child *,
        [data-testid="stExpander"] > details > summary,
        [data-testid="stExpander"] > details > summary * {{
            color: var(--kozade-button-text) !important;
            fill: var(--kozade-button-text) !important;
        }}

        [data-testid="stStatusWidget"] > div:first-child,
        [data-testid="stExpander"] > details > summary {{
            background: var(--kozade-button-bg) !important;
        }}

        [data-testid="stMetric"] {{
            background: var(--kozade-card);
            border: 1px solid var(--kozade-line);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }}

        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {{
            color: var(--kozade-ink);
        }}

        [data-testid="stDataFrame"] {{
            background: var(--kozade-card);
            border: 1px solid var(--kozade-line);
            border-radius: 8px;
            overflow: hidden;
        }}

        .stAlert {{
            background: var(--kozade-card);
            color: var(--kozade-ink);
            border-color: var(--kozade-line);
        }}

        @media (max-width: 760px) {{
            .kozade-logo {{
                position: static;
                display: block;
                width: 118px;
                margin: 0 0 1.25rem auto;
            }}

            .block-container {{
                padding-top: 2rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}
        }}
        </style>
        {logo_markup}
        """,
        unsafe_allow_html=True,
    )


apply_kozade_theme()


def request_page(url):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )

    try:
        with urlopen(request, timeout=25) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"Sayfa açılamadı. HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Bağlantı kurulamadı: {exc.reason}") from exc


def post_json(url, payload, headers=None):
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "Origin": "https://nekadarsatti.com",
        "Referer": "https://nekadarsatti.com/",
    }
    request_headers.update(headers or {})
    request = Request(url, data=body, headers=request_headers, method="POST")

    try:
        with urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        charset = exc.headers.get_content_charset() or "utf-8"
        error_body = exc.read().decode(charset, errors="replace")
        return exc.code, error_body
    except URLError as exc:
        raise RuntimeError(f"Nekadarsatti bağlantısı kurulamadı: {exc.reason}") from exc


def request_json(url, params=None):
    query = urlencode(params or {})
    request_url = f"{url}?{query}" if query else url
    request = Request(
        request_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": TRENDYOL_BASE,
            "Referer": f"{TRENDYOL_BASE}/",
        },
    )

    try:
        with urlopen(request, timeout=25) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset, errors="replace"))
    except HTTPError as exc:
        raise RuntimeError(f"API açılamadı. HTTP {exc.code}: {request_url}") from exc
    except URLError as exc:
        raise RuntimeError(f"API bağlantısı kurulamadı: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("API JSON olmayan cevap döndürdü.") from exc


def validate_trendyol_url(product_url):
    parsed_url = urlparse(product_url.strip())

    if parsed_url.scheme not in ["http", "https"]:
        raise ValueError("Link http veya https ile başlamalı.")

    if "trendyol.com" not in parsed_url.netloc.lower():
        raise ValueError("Bu alan adı Trendyol değil.")

    if "-p-" not in parsed_url.path:
        raise ValueError("Bu link Trendyol ürün linki gibi görünmüyor.")

    return product_url.strip()


def fetch_page(product_url):
    return request_page(product_url)


def extract_product_id(value):
    if not value:
        return None
    match = re.search(r"-p-(\d+)", str(value))
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{6,})\b", str(value))
    return match.group(1) if match else None


def clean_text(value):
    if value is None:
        return None
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def parse_compact_number(value):
    if value is None:
        return None

    text = str(value).strip().lower()
    text = text.replace("+", "").replace(" ", "")
    multiplier = 1
    if text.endswith(("k", "b")):
        multiplier = 1000
        text = text[:-1]
    elif text.endswith(("m", "mn")):
        multiplier = 1000000
        text = text.removesuffix("mn").removesuffix("m")

    text = text.replace(".", "").replace(",", ".")
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def best_number_match(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return parse_compact_number(match.group(1))
    return None


def with_category_query(category_url, page_no, sort_value="BEST_SELLER"):
    parsed = urlparse(category_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if sort_value:
        query["sst"] = sort_value
    query["pi"] = str(page_no)
    return urlunparse(parsed._replace(query=urlencode(query)))


def brand_search_url(brand_name):
    brand = brand_name.strip()
    query = urlencode({"q": brand, "qt": brand, "st": brand, "os": "1"})
    return f"{TRENDYOL_BASE}/sr?{query}"


def discover_search_products(search_text, pages, limit):
    products = []
    seen = set()

    for page_no in range(1, pages + 1):
        payload = request_json(
            TRENDYOL_SEARCH_API_URL,
            {
                "q": search_text,
                "pi": page_no,
                "culture": "tr-TR",
                "userGenderId": "1",
                "pId": "0",
                "scoringAlgorithmId": "2",
                "categoryRelevancyEnabled": "false",
                "isLegalRequirementConfirmed": "false",
                "searchStrategyType": "DEFAULT",
                "productStampType": "A",
                "fixSlotProductAdsIncluded": "false",
                "searchAbDeciderValues": "",
            },
        )
        page_products = payload.get("result", {}).get("products") or []
        if not page_products:
            break

        for item in page_products:
            if not isinstance(item, dict):
                continue
            product_id = item.get("id") or item.get("productId")
            product_url = item.get("url") or item.get("productUrl")
            if not product_id and product_url:
                product_id = extract_product_id(product_url)
            if not product_id or str(product_id) in seen:
                continue

            seen.add(str(product_id))
            products.append(
                {
                    "Sıra": len(products) + 1,
                    "Ürün ID": str(product_id),
                    "Ürün": item.get("name") or item.get("title") or "Trendyol ürünü",
                    "Liste etiketi": None,
                    "Link": normalize_product_url(product_url or f"/p-{product_id}"),
                }
            )
            if len(products) >= limit:
                return products

    return products


def normalize_product_url(raw_url):
    raw_url = html.unescape(raw_url).replace("\\/", "/").strip()
    raw_url = raw_url.split("?")[0]
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    elif raw_url.startswith("/"):
        raw_url = urljoin(TRENDYOL_BASE, raw_url)
    elif not raw_url.startswith("http"):
        raw_url = urljoin(TRENDYOL_BASE, "/" + raw_url.lstrip("/"))
    return raw_url


def extract_title_from_context(context):
    context = html.unescape(context).replace("\\/", "/")
    candidates = []
    patterns = [
        r'"name"\s*:\s*"([^"]{3,180})"',
        r'"title"\s*:\s*"([^"]{3,180})"',
        r'class="[^"]*prdct-desc-cntnr-name[^"]*"[^>]*>(.*?)<',
        r'class="[^"]*prdct-desc-cntnr-ttl[^"]*"[^>]*>(.*?)<',
        r'title="([^"]{3,180})"',
    ]
    for pattern in patterns:
        candidates.extend(re.findall(pattern, context, flags=re.IGNORECASE | re.DOTALL))

    cleaned = [clean_text(candidate) for candidate in candidates]
    cleaned = [candidate for candidate in cleaned if candidate and "-p-" not in candidate]
    return cleaned[0] if cleaned else "Trendyol ürünü"


def extract_listing_badge(context):
    text = clean_text(context) or ""
    patterns = [
        r"En\s+Çok\s+Satan\s+\d+\.?\s*Ürün",
        r"En\s+Çok\s+Ziyaret\s+Edilen\s+\d+\.?\s*Ürün",
        r"En\s+Çok\s+Değerlendirilen\s+\d+\.?\s*Ürün",
        r"En\s+Çok\s+Favorilenen\s+\d+\.?\s*Ürün",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def discover_category_products(category_url, pages, limit, sort_value="BEST_SELLER"):
    products = []
    seen = set()
    last_error = None

    for page_no in range(1, pages + 1):
        try:
            source = request_page(with_category_query(category_url, page_no, sort_value))
        except RuntimeError as exc:
            last_error = exc
            if products:
                break
            raise

        decoded = html.unescape(source).replace("\\/", "/")
        link_matches = list(re.finditer(r'(?:"url"\s*:\s*"|href=["\'])([^"\']*-p-\d+[^"\']*)', decoded))

        for match in link_matches:
            product_url = normalize_product_url(match.group(1))
            product_id = extract_product_id(product_url)
            if not product_id or product_id in seen:
                continue

            seen.add(product_id)
            context = decoded[max(0, match.start() - 900) : min(len(decoded), match.end() + 900)]
            products.append(
                {
                    "Sıra": len(products) + 1,
                    "Ürün ID": product_id,
                    "Ürün": extract_title_from_context(context),
                    "Liste etiketi": extract_listing_badge(context),
                    "Link": product_url,
                }
            )
            if len(products) >= limit:
                return products

    if last_error and not products:
        raise last_error
    return products


def discover_category_brands(category_url):
    try:
        source = request_page(with_category_query(category_url, 1))
    except Exception:
        return []

    decoded = html.unescape(source).replace("\\/", "/")
    brands = set()
    patterns = [
        r'"brand"\s*:\s*\{[^{}]*"name"\s*:\s*"([^"]{2,80})"',
        r'"webBrand"\s*:\s*\{[^{}]*"name"\s*:\s*"([^"]{2,80})"',
        r'"brandName"\s*:\s*"([^"]{2,80})"',
        r'"name"\s*:\s*"([^"]{2,80})"[^{}]{0,120}"filterField"\s*:\s*"brand"',
    ]
    for pattern in patterns:
        for match in re.findall(pattern, decoded, flags=re.IGNORECASE):
            brand = clean_text(match)
            if brand and not any(blocked in brand.lower() for blocked in ["trendyol", "online alışveriş"]):
                brands.add(brand)

    return sorted(brands, key=str.casefold)[:80]


def extract_balanced_json(text, marker):
    marker_index = text.find(marker)
    if marker_index == -1:
        return None

    start_index = text.find("{", marker_index)
    if start_index == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start_index, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]

    return None


def load_envoy_props(source_text):
    decoded_text = html.unescape(source_text)

    for marker in ENVoy_MARKERS:
        raw_json = extract_balanced_json(decoded_text, marker)
        if raw_json:
            return json.loads(raw_json)

    stripped_text = decoded_text.strip().rstrip(";")
    if stripped_text.startswith("{"):
        return json.loads(stripped_text)

    raise ValueError('Kaynak içinde `window["__envoy_product-info__PROPS"]` JSON verisi bulunamadı.')


def format_price(price):
    if isinstance(price, dict):
        for key in ["discountedPrice", "sellingPrice", "originalPrice", "price", "text", "value"]:
            if key in price and price[key] not in [None, ""]:
                return format_price(price[key])
    if isinstance(price, (int, float)):
        return f"{price:,.2f} TL"
    if isinstance(price, str):
        return price
    return None


def stock_status(in_stock, quantity):
    if in_stock is False or quantity == 0:
        return "Stokta yok"
    if in_stock is True or isinstance(quantity, (int, float)):
        return "Stokta"
    return "Bilinmiyor"


def product_summary(props):
    product = props.get("product", {})
    brand = product.get("brand") if isinstance(product.get("brand"), dict) else {}
    images = product.get("images") or []
    rating_score = product.get("ratingScore") if isinstance(product.get("ratingScore"), dict) else {}
    category_rankings = product.get("categoryTopRankings") or []
    best_seller_rank = None
    for ranking in category_rankings:
        if isinstance(ranking, dict) and ranking.get("name") == "bestSeller":
            best_seller_rank = ranking.get("order")
            break

    return {
        "Ürün": product.get("name", "Trendyol ürünü"),
        "Marka": brand.get("name") or product.get("brandName"),
        "Ürün ID": product.get("id"),
        "Stokta": product.get("inStock"),
        "Görsel": images[0] if images else None,
        "Favori": product.get("favoriteCount"),
        "Yorum": rating_score.get("commentCount"),
        "Değerlendirme": rating_score.get("totalCount"),
        "Puan": rating_score.get("averageRating"),
        "Çok satan sıra": best_seller_rank,
    }


def extract_trendyol_signal_summary(source_text, props):
    product = props.get("product", {})
    decoded_text = clean_text(source_text) or ""
    visible_text = decoded_text.replace("\\u002F", "/")

    sales_3d = best_number_match(
        [
            r"3\s*g[üu]nde\s*([\d.,]+(?:k|b|m|mn)?\+?)\s*sat[ıi]ş",
            r"3\s*g[üu]nde\s*([\d.,]+(?:k|b|m|mn)?\+?)\s*[üu]r[üu]n\s*sat[ıi]ld[ıi]",
            r"son\s*3\s*g[üu]nde\s*([\d.,]+(?:k|b|m|mn)?\+?)\s*sat[ıi]ş",
            r"son\s*3\s*g[üu]nde\s*([\d.,]+(?:k|b|m|mn)?\+?)\s*[üu]r[üu]n\s*sat[ıi]ld[ıi]",
        ],
        visible_text,
    )
    views_1d = best_number_match(
        [
            r"1\s*g[üu]nde\s*([\d.,]+(?:k|b|m|mn)?\+?)\s*kişi\s*g[öo]r[üu]nt[üu]ledi",
            r"([\d.,]+(?:k|b|m|mn)?\+?)\s*kişi\s*1\s*g[üu]nde\s*g[öo]r[üu]nt[üu]ledi",
        ],
        visible_text,
    )
    basket_count = best_number_match(
        [
            r"([\d.,]+(?:k|b|m|mn)?\+?)\s*kişinin\s*sepetinde",
            r"([\d.,]+(?:k|b|m|mn)?\+?)\s*kişi\s*sepet",
        ],
        visible_text,
    )

    rating_score = product.get("ratingScore") if isinstance(product.get("ratingScore"), dict) else {}
    category_rankings = product.get("categoryTopRankings") or []
    best_seller_rank = None
    for ranking in category_rankings:
        if isinstance(ranking, dict) and ranking.get("name") == "bestSeller":
            best_seller_rank = ranking.get("order")
            break

    return {
        "3 günlük satış ibaresi": sales_3d,
        "1 günlük görüntülenme ibaresi": views_1d,
        "Sepet ibaresi": basket_count,
        "Favori": product.get("favoriteCount"),
        "Yorum": rating_score.get("commentCount"),
        "Değerlendirme": rating_score.get("totalCount"),
        "Puan": rating_score.get("averageRating"),
        "Çok satan sıra": best_seller_rank,
    }


def variant_label(variant):
    label = variant.get("beautifiedValue") or variant.get("value")
    return label if label else "Ana varyant"


def seller_rows(props):
    product = props.get("product", {})
    listing = product.get("merchantListing", {})
    rows = []

    winner_variant = listing.get("winnerVariant")
    main_merchant = listing.get("merchant", {})
    if isinstance(winner_variant, dict):
        rows.append(make_row(main_merchant, winner_variant, "Seçili satıcı", listing.get("price")))

    for merchant in listing.get("otherMerchants", []):
        if not isinstance(merchant, dict):
            continue
        for variant in merchant.get("variants", []):
            if isinstance(variant, dict):
                rows.append(make_row(merchant, variant, "Diğer satıcı", merchant.get("price")))

    seen = set()
    unique_rows = []
    for row in rows:
        signature = (row["Satıcı ID"], row["Listing ID"], row["Quantity"])
        if signature in seen:
            continue
        seen.add(signature)
        unique_rows.append(row)

    return unique_rows


def make_row(merchant, variant, source, fallback_price):
    quantity = variant.get("quantity")

    return {
        "Satıcı": merchant.get("name") or "Bilinmeyen satıcı",
        "Satıcı ID": merchant.get("id"),
        "Varyant": variant_label(variant),
        "Quantity": quantity,
        "Stok durumu": stock_status(variant.get("inStock"), quantity),
        "Fiyat": format_price(variant.get("price") or fallback_price),
        "Maks. satış": variant.get("maxSaleLimit"),
        "Listing ID": variant.get("listingId"),
        "Kaynak": source,
    }


def raw_quantity_matches(source_text):
    rows = []
    decoded_text = html.unescape(source_text)

    for index, match in enumerate(re.finditer(r'"quantity"\s*:\s*(-?\d+(?:\.\d+)?)', decoded_text), start=1):
        quantity_text = match.group(1)
        quantity = float(quantity_text) if "." in quantity_text else int(quantity_text)
        context = decoded_text[max(0, match.start() - 90) : min(len(decoded_text), match.end() + 90)]
        rows.append(
            {
                "Sıra": index,
                "Quantity": quantity,
                "Bağlam": re.sub(r"\s+", " ", context).strip(),
            }
        )

    return rows


def analyze_source(source_text):
    props = load_envoy_props(source_text)
    summary = product_summary(props)
    rows = seller_rows(props)
    raw_rows = raw_quantity_matches(source_text)

    if not rows and raw_rows:
        rows = [
            {
                "Satıcı": "Kaynak metin",
                "Satıcı ID": None,
                "Varyant": "Bulunan quantity",
                "Quantity": raw_rows[0]["Quantity"],
                "Stok durumu": stock_status(True, raw_rows[0]["Quantity"]),
                "Fiyat": None,
                "Maks. satış": None,
                "Listing ID": None,
                "Kaynak": "Regex",
            }
        ]

    return summary, rows, raw_rows


def analyze_trendyol_signals(source_text):
    props = load_envoy_props(source_text)
    return extract_trendyol_signal_summary(source_text, props)


def parse_sales_dataframe(df):
    if df.empty:
        return {}

    lower_map = {str(column).strip().lower(): column for column in df.columns}
    id_column = next(
        (
            lower_map[name]
            for name in ["ürün id", "urun id", "product_id", "product id", "id", "ty id"]
            if name in lower_map
        ),
        None,
    )
    url_column = next((lower_map[name] for name in ["link", "url", "ürün linki", "urun linki"] if name in lower_map), None)
    sales_column = next(
        (
            lower_map[name]
            for name in [
                "3 günlük satış",
                "3 gunluk satis",
                "son 3 gün",
                "son 3 gun",
                "sales_3d",
                "satis_3g",
                "satış",
                "satis",
                "adet",
            ]
            if name in lower_map
        ),
        None,
    )

    if not sales_column:
        numeric_columns = [
            column
            for column in df.columns
            if pd.to_numeric(df[column], errors="coerce").notna().any()
        ]
        sales_column = numeric_columns[-1] if numeric_columns else None

    if not id_column and not url_column:
        raise ValueError("Satış verisinde ürün ID veya Trendyol linki kolonu bulunmalı.")
    if not sales_column:
        raise ValueError("Satış verisinde 3 günlük satış adedi kolonu bulunmalı.")

    sales_map = {}
    for _, row in df.iterrows():
        product_id = extract_product_id(row.get(id_column)) if id_column else None
        if not product_id and url_column:
            product_id = extract_product_id(row.get(url_column))
        sales_count = pd.to_numeric(row.get(sales_column), errors="coerce")
        if product_id and pd.notna(sales_count):
            sales_map[str(product_id)] = int(sales_count)

    return sales_map


def parse_sales_text(raw_text):
    if not raw_text.strip():
        return {}

    rows = []
    for line in raw_text.splitlines():
        product_id = extract_product_id(line)
        numbers = re.findall(r"\b\d+\b", line)
        if product_id and numbers:
            sales_candidates = [int(number) for number in numbers if number != product_id]
            if sales_candidates:
                rows.append({"Ürün ID": product_id, "3 günlük satış": sales_candidates[-1]})

    return parse_sales_dataframe(pd.DataFrame(rows)) if rows else {}


def load_sales_map(uploaded_file, pasted_text):
    sales_map = {}

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        text = content.decode("utf-8-sig", errors="replace")
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample.strip() else csv.excel
            df = pd.read_csv(io.StringIO(text), dialect=dialect)
        except csv.Error:
            df = pd.read_csv(io.StringIO(text))
        sales_map.update(parse_sales_dataframe(df))

    sales_map.update(parse_sales_text(pasted_text))
    return sales_map


def parse_nekadarsatti_response(product, response_text):
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Nekadarsatti JSON olmayan cevap döndürdü.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Nekadarsatti cevabı beklenen formatta değil.")

    order = payload.get("order")
    sales_count = pd.to_numeric(order, errors="coerce")
    if pd.isna(sales_count):
        raise ValueError("Nekadarsatti cevabında satış adedi bulunamadı.")

    return {
        "Ürün ID": str(product["Ürün ID"]),
        "Ürün": payload.get("name") or product["Ürün"],
        "3 günlük satış": int(sales_count),
        "Fiyat": payload.get("price"),
        "Ciro": int(sales_count) * payload["price"] if isinstance(payload.get("price"), (int, float)) else None,
        "Görüntülenme": payload.get("pageViewCount"),
        "Sepette": payload.get("basketCount"),
        "Favori": payload.get("favoriteCount"),
        "Link": product["Link"],
    }


def fetch_nekadarsatti_sales(product):
    status, response_text = post_json(
        NEKADARSATTI_API_URL,
        {"productUrl": product["Link"]},
        headers={"x-api-key": NEKADARSATTI_PUBLIC_API_KEY},
    )

    if status >= 400:
        try:
            payload = json.loads(response_text)
            message = payload.get("error") or payload.get("message") or response_text
        except json.JSONDecodeError:
            message = clean_text(response_text) or "Bilinmeyen hata"
        raise RuntimeError(f"Nekadarsatti HTTP {status}: {message}")

    return parse_nekadarsatti_response(product, response_text)


def fetch_nekadarsatti_sales_map(products, limit, delay_seconds, status_container):
    limited_products = products[: min(limit, NEKADARSATTI_QUERY_LIMIT)]
    sales_rows = []
    sales_errors = []

    for index, product in enumerate(limited_products, start=1):
        status_container.write(f"Nekadarsatti {index}/{len(limited_products)}: {product['Ürün ID']}")
        try:
            sales_rows.append(fetch_nekadarsatti_sales(product))
        except Exception as exc:
            sales_errors.append(
                {
                    "Ürün ID": product["Ürün ID"],
                    "Ürün": product["Ürün"],
                    "Hata": str(exc),
                    "Link": product["Link"],
                }
            )
        if index < len(limited_products) and delay_seconds > 0:
            time.sleep(delay_seconds)

    sales_map = {
        row["Ürün ID"]: row["3 günlük satış"]
        for row in sales_rows
        if row.get("Ürün ID") and row.get("3 günlük satış") is not None
    }
    return sales_map, sales_rows, sales_errors


def find_opportunities(products, sales_map, seller_filter, skip_without_sales, progress):
    opportunity_rows = []
    checked_rows = []
    errors = []

    for index, product in enumerate(products, start=1):
        progress.progress(index / max(len(products), 1), text=f"{index}/{len(products)} kontrol ediliyor")
        product_id = str(product["Ürün ID"])
        sales_3d = sales_map.get(product_id)

        if sales_3d is None and skip_without_sales:
            checked_rows.append({**product, "Durum": "Satış verisi yok"})
            continue

        try:
            source = fetch_page(product["Link"])
            summary, rows, _ = analyze_source(source)
        except Exception as exc:
            errors.append({"Ürün ID": product_id, "Ürün": product["Ürün"], "Hata": str(exc), "Link": product["Link"]})
            continue

        for row in rows:
            seller_name = str(row.get("Satıcı") or "")
            if seller_filter and seller_filter.casefold() not in seller_name.casefold():
                continue

            quantity = pd.to_numeric(row.get("Quantity"), errors="coerce")
            is_numeric_stock = pd.notna(quantity)
            is_opportunity = sales_3d is not None and is_numeric_stock and int(quantity) <= int(sales_3d)
            record = {
                "Sıra": product["Sıra"],
                "Ürün ID": product_id,
                "Ürün": summary.get("Ürün") or product["Ürün"],
                "Marka": summary.get("Marka"),
                "Liste etiketi": product.get("Liste etiketi"),
                "Satıcı": row.get("Satıcı"),
                "Varyant": row.get("Varyant"),
                "Stok": int(quantity) if is_numeric_stock else None,
                "3 günlük satış": sales_3d,
                "Fırsat": "Evet" if is_opportunity else "Hayır",
                "Fiyat": row.get("Fiyat"),
                "Listing ID": row.get("Listing ID"),
                "Link": product["Link"],
            }
            checked_rows.append(record)
            if is_opportunity:
                opportunity_rows.append(record)

    progress.empty()
    return opportunity_rows, checked_rows, errors


def brand_matches(brand_name, selected_brands, custom_brand_filter):
    filters = [brand.casefold() for brand in selected_brands if brand]
    filters.extend(
        brand.strip().casefold()
        for brand in custom_brand_filter.split(",")
        if brand.strip()
    )
    if not filters:
        return True

    normalized_brand = str(brand_name or "").casefold()
    return any(brand in normalized_brand for brand in filters)


def signal_hit(signal, min_sales_3d, min_views_1d, min_basket, min_favorite, max_best_rank):
    hits = []
    sales_3d = pd.to_numeric(signal.get("3 günlük satış ibaresi"), errors="coerce")
    views_1d = pd.to_numeric(signal.get("1 günlük görüntülenme ibaresi"), errors="coerce")
    basket = pd.to_numeric(signal.get("Sepet ibaresi"), errors="coerce")
    favorite = pd.to_numeric(signal.get("Favori"), errors="coerce")
    best_rank = pd.to_numeric(signal.get("Çok satan sıra"), errors="coerce")

    if min_sales_3d is not None and pd.notna(sales_3d) and int(sales_3d) >= min_sales_3d:
        hits.append(f"3g satış {int(sales_3d)}+")
    if min_views_1d is not None and pd.notna(views_1d) and int(views_1d) >= min_views_1d:
        hits.append(f"1g görüntülenme {int(views_1d)}+")
    if min_basket is not None and pd.notna(basket) and int(basket) >= min_basket:
        hits.append(f"sepette {int(basket)}+")
    if min_favorite is not None and pd.notna(favorite) and int(favorite) >= min_favorite:
        hits.append(f"favori {int(favorite)}+")
    if max_best_rank is not None and pd.notna(best_rank) and int(best_rank) <= max_best_rank:
        hits.append(f"çok satan sıra {int(best_rank)}")

    return hits


def find_signal_opportunities(
    products,
    seller_filter,
    selected_brands,
    custom_brand_filter,
    max_stock,
    min_sales_3d,
    min_views_1d,
    min_basket,
    min_favorite,
    max_best_rank,
    progress,
):
    opportunity_rows = []
    checked_rows = []
    errors = []

    for index, product in enumerate(products, start=1):
        progress.progress(index / max(len(products), 1), text=f"{index}/{len(products)} sinyal kontrol ediliyor")
        product_id = str(product["Ürün ID"])

        try:
            source = fetch_page(product["Link"])
            summary, rows, _ = analyze_source(source)
        except Exception as exc:
            errors.append({"Ürün ID": product_id, "Ürün": product["Ürün"], "Hata": str(exc), "Link": product["Link"]})
            continue

        if not brand_matches(summary.get("Marka"), selected_brands, custom_brand_filter):
            continue

        hits = signal_hit(signal, min_sales_3d, min_views_1d, min_basket, min_favorite, max_best_rank)
        seller_records = []

        for row in rows:
            seller_name = str(row.get("Satıcı") or "")
            if seller_filter and seller_filter.casefold() not in seller_name.casefold():
                continue

            quantity = pd.to_numeric(row.get("Quantity"), errors="coerce")
            is_numeric_stock = pd.notna(quantity)
            stock_value = int(quantity) if is_numeric_stock else None
            seller_records.append(
                {
                    "row": row,
                    "stock": stock_value,
                }
            )

        valid_stocks = [record["stock"] for record in seller_records if record["stock"] is not None]
        max_product_stock = max(valid_stocks) if valid_stocks else None
        top_stock_record = None
        if max_product_stock is not None:
            top_stock_record = next(
                (record for record in seller_records if record["stock"] == max_product_stock),
                None,
            )
        product_is_opportunity = bool(hits) and max_product_stock is not None and max_product_stock <= max_stock

        for seller_record in seller_records:
            row = seller_record["row"]
            stock_value = seller_record["stock"]
            is_top_stock_row = product_is_opportunity and top_stock_record is not None and row is top_stock_record["row"]
            record = {
                "Sıra": product["Sıra"],
                "Ürün ID": product_id,
                "Ürün": summary.get("Ürün") or product["Ürün"],
                "Marka": summary.get("Marka"),
                "Liste etiketi": product.get("Liste etiketi"),
                "Satıcı": row.get("Satıcı"),
                "Varyant": row.get("Varyant"),
                "Stok": stock_value,
                "Ürün max stok": max_product_stock,
                "Max stok satıcısı": top_stock_record["row"].get("Satıcı") if top_stock_record else None,
                "Fırsat": "Evet" if product_is_opportunity else "Hayır",
                "Sinyal": ", ".join(hits) if hits else "-",
                "3g satış ibaresi": signal.get("3 günlük satış ibaresi"),
                "1g görüntülenme": signal.get("1 günlük görüntülenme ibaresi"),
                "Sepette": signal.get("Sepet ibaresi"),
                "Favori": signal.get("Favori"),
                "Yorum": signal.get("Yorum"),
                "Değerlendirme": signal.get("Değerlendirme"),
                "Çok satan sıra": signal.get("Çok satan sıra"),
                "Fiyat": row.get("Fiyat"),
                "Listing ID": row.get("Listing ID"),
                "Link": product["Link"],
            }
            checked_rows.append(record)
            if is_top_stock_row:
                opportunity_rows.append(record)

    progress.empty()
    return opportunity_rows, checked_rows, errors


def find_brand_stock_products(
    products,
    seller_filter,
    selected_brands,
    custom_brand_filter,
    max_stock,
    progress,
    start_index=0,
    batch_size=None,
):
    checked_rows = []
    errors = []
    stats = {
        "Ürün kontrol": 0,
        "Marka eşleşti": 0,
        "Stok okunabildi": 0,
        "Stok eşiği üstü": 0,
    }
    end_index = len(products) if batch_size is None else min(len(products), start_index + batch_size)
    batch_products = products[start_index:end_index]

    for index, product in enumerate(batch_products, start=start_index + 1):
        progress.progress(index / max(len(products), 1), text=f"{index}/{len(products)} marka/stok kontrol ediliyor")
        product_id = str(product["Ürün ID"])
        stats["Ürün kontrol"] += 1

        try:
            source = fetch_page(product["Link"])
            summary, rows, _ = analyze_source(source)
            signal = analyze_trendyol_signals(source)
        except Exception as exc:
            errors.append({"Ürün ID": product_id, "Ürün": product["Ürün"], "Hata": str(exc), "Link": product["Link"]})
            continue

        if not brand_matches(summary.get("Marka"), selected_brands, custom_brand_filter):
            continue
        stats["Marka eşleşti"] += 1

        seller_records = []
        for row in rows:
            seller_name = str(row.get("Satıcı") or "")
            if seller_filter and seller_filter.casefold() not in seller_name.casefold():
                continue

            quantity = pd.to_numeric(row.get("Quantity"), errors="coerce")
            stock_value = int(quantity) if pd.notna(quantity) else None
            seller_records.append({"row": row, "stock": stock_value})

        valid_stocks = [record["stock"] for record in seller_records if record["stock"] is not None]
        max_product_stock = max(valid_stocks) if valid_stocks else None
        if max_product_stock is None or max_product_stock > max_stock:
            if max_product_stock is not None:
                stats["Stok okunabildi"] += 1
                stats["Stok eşiği üstü"] += 1
            continue
        stats["Stok okunabildi"] += 1

        top_stock_record = next(
            (record for record in seller_records if record["stock"] == max_product_stock),
            None,
        )

        for seller_record in seller_records:
            row = seller_record["row"]
            record = {
                "Sıra": product["Sıra"],
                "Ürün ID": product_id,
                "Ürün": summary.get("Ürün") or product["Ürün"],
                "Marka": summary.get("Marka"),
                "Liste etiketi": product.get("Liste etiketi"),
                "Satıcı": row.get("Satıcı"),
                "Varyant": row.get("Varyant"),
                "Stok": seller_record["stock"],
                "Ürün max stok": max_product_stock,
                "Max stok satıcısı": top_stock_record["row"].get("Satıcı") if top_stock_record else None,
                "Fırsat": "Evet",
                "Favori": summary.get("Favori"),
                "Yorum": summary.get("Yorum"),
                "Değerlendirme": summary.get("Değerlendirme"),
                "Fiyat": row.get("Fiyat"),
                "Listing ID": row.get("Listing ID"),
                "Link": product["Link"],
            }
            checked_rows.append(record)

    progress.empty()
    return checked_rows, errors, stats, end_index


def check_brand_stock_product(product, selected_brands, custom_brand_filter, seller_filter, max_stock):
    product_id = str(product["Ürün ID"])
    stats = {
        "Ürün kontrol": 1,
        "Marka eşleşti": 0,
        "Stok okunabildi": 0,
        "Stok eşiği üstü": 0,
    }

    try:
        source = fetch_page(product["Link"])
        summary, rows, _ = analyze_source(source)
    except Exception as exc:
        return [], [{"Ürün ID": product_id, "Ürün": product["Ürün"], "Hata": str(exc), "Link": product["Link"]}], stats

    if not brand_matches(summary.get("Marka"), selected_brands, custom_brand_filter):
        return [], [], stats
    stats["Marka eşleşti"] += 1

    seller_records = []
    for row in rows:
        seller_name = str(row.get("Satıcı") or "")
        if seller_filter and seller_filter.casefold() not in seller_name.casefold():
            continue

        quantity = pd.to_numeric(row.get("Quantity"), errors="coerce")
        stock_value = int(quantity) if pd.notna(quantity) else None
        seller_records.append({"row": row, "stock": stock_value})

    valid_stocks = [record["stock"] for record in seller_records if record["stock"] is not None]
    max_product_stock = max(valid_stocks) if valid_stocks else None
    if max_product_stock is None or max_product_stock > max_stock:
        if max_product_stock is not None:
            stats["Stok okunabildi"] += 1
            stats["Stok eşiği üstü"] += 1
        return [], [], stats
    stats["Stok okunabildi"] += 1

    top_stock_record = next(
        (record for record in seller_records if record["stock"] == max_product_stock),
        None,
    )
    checked_rows = []
    for seller_record in seller_records:
        row = seller_record["row"]
        checked_rows.append(
            {
                "Sıra": product["Sıra"],
                "Ürün ID": product_id,
                "Ürün": summary.get("Ürün") or product["Ürün"],
                "Marka": summary.get("Marka"),
                "Liste etiketi": product.get("Liste etiketi"),
                "Satıcı": row.get("Satıcı"),
                "Varyant": row.get("Varyant"),
                "Stok": seller_record["stock"],
                "Ürün max stok": max_product_stock,
                "Max stok satıcısı": top_stock_record["row"].get("Satıcı") if top_stock_record else None,
                "Fırsat": "Evet",
                "Favori": summary.get("Favori"),
                "Yorum": summary.get("Yorum"),
                "Değerlendirme": summary.get("Değerlendirme"),
                "Fiyat": row.get("Fiyat"),
                "Listing ID": row.get("Listing ID"),
                "Link": product["Link"],
            }
        )

    return checked_rows, [], stats


def find_brand_stock_products_parallel(
    products,
    seller_filter,
    selected_brands,
    custom_brand_filter,
    max_stock,
    progress,
    live_container,
    existing_checked=None,
    start_index=0,
    batch_size=None,
    workers=8,
):
    checked_rows = []
    errors = []
    stats = {
        "Ürün kontrol": 0,
        "Marka eşleşti": 0,
        "Stok okunabildi": 0,
        "Stok eşiği üstü": 0,
    }
    end_index = len(products) if batch_size is None else min(len(products), start_index + batch_size)
    batch_products = products[start_index:end_index]
    completed = start_index
    preview_rows = list(existing_checked or [])[-80:]

    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as executor:
        futures = {
            executor.submit(
                check_brand_stock_product,
                product,
                selected_brands,
                custom_brand_filter,
                seller_filter,
                max_stock,
            ): product
            for product in batch_products
        }
        for future in as_completed(futures):
            completed += 1
            product_checked, product_errors, product_stats = future.result()
            checked_rows.extend(product_checked)
            errors.extend(product_errors)
            stats = merge_stats(stats, product_stats)
            if product_checked:
                preview_rows.extend(product_checked)
                preview_df = product_summary_rows(pd.DataFrame(preview_rows), include_signal_columns=False)
                if not preview_df.empty:
                    live_container.dataframe(
                        display_product_links(preview_df),
                        use_container_width=True,
                        hide_index=True,
                        column_config=product_link_column_config(),
                    )
            progress.progress(completed / max(len(products), 1), text=f"{completed}/{len(products)} marka/stok kontrol ediliyor")

    progress.empty()
    return checked_rows, errors, stats, end_index


def unique_products(products):
    seen = set()
    unique_rows = []
    for product in products:
        product_id = str(product.get("Ürün ID") or "")
        link = product.get("Link")
        signature = product_id or link
        if not signature or signature in seen:
            continue
        seen.add(signature)
        unique_rows.append({**product, "Sıra": len(unique_rows) + 1})
    return unique_rows


def dataframe_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def first_present(series):
    for value in series:
        if pd.notna(value) and value not in [None, ""]:
            return value
    return None


def merge_stats(base, addition):
    merged = dict(base or {})
    for key, value in (addition or {}).items():
        merged[key] = int(merged.get(key, 0)) + int(value or 0)
    return merged


def product_summary_rows(checked_df, include_signal_columns=True):
    if checked_df.empty or "Ürün ID" not in checked_df.columns:
        return pd.DataFrame()

    summary_rows = []
    for product_id, group in checked_df.groupby("Ürün ID", dropna=False):
        stock_series = pd.to_numeric(group.get("Stok"), errors="coerce")
        stock_rows = group[stock_series.notna()].copy()

        top_seller = None
        top_stock = None
        total_stock = None
        other_stocks = None
        seller_stock_text = None

        if not stock_rows.empty:
            stock_rows["_stock_numeric"] = pd.to_numeric(stock_rows["Stok"], errors="coerce")
            stock_rows = stock_rows.sort_values("_stock_numeric", ascending=False)
            top_row = stock_rows.iloc[0]
            top_seller = top_row.get("Satıcı")
            top_stock = int(top_row["_stock_numeric"])
            total_stock = int(stock_rows["_stock_numeric"].dropna().sum())
            other_values = [str(int(value)) for value in stock_rows["_stock_numeric"].iloc[1:].dropna()]
            other_stocks = "/".join(other_values) if other_values else None
            seller_stock_text = f"{top_seller}: {top_stock}"
            if other_stocks:
                seller_stock_text = f"{seller_stock_text} / {other_stocks}"

        summary_row = {
            "Ürün ID": product_id,
            "Ürün": first_present(group.get("Ürün", pd.Series(dtype=object))),
            "Marka": first_present(group.get("Marka", pd.Series(dtype=object))),
            "Liste etiketi": first_present(group.get("Liste etiketi", pd.Series(dtype=object))),
            "En yüksek stok satıcısı": top_seller,
            "En yüksek stok": top_stock,
            "Toplam stok": total_stock,
            "Max stok satıcısı": first_present(group.get("Max stok satıcısı", pd.Series(dtype=object))) or top_seller,
            "Diğer stoklar": other_stocks,
            "Satıcı stokları": seller_stock_text,
            "Favori": first_present(group.get("Favori", pd.Series(dtype=object))),
            "Yorum": first_present(group.get("Yorum", pd.Series(dtype=object))),
            "Değerlendirme": first_present(group.get("Değerlendirme", pd.Series(dtype=object))),
            "Fırsat satırı var": "Evet" if (group.get("Fırsat", pd.Series(dtype=object)) == "Evet").any() else "Hayır",
            "Link": first_present(group.get("Link", pd.Series(dtype=object))),
        }
        if include_signal_columns:
            summary_row.update(
                {
                    "3 günlük satış": first_present(group.get("3 günlük satış", pd.Series(dtype=object))),
                    "3g satış ibaresi": first_present(group.get("3g satış ibaresi", pd.Series(dtype=object))),
                    "1g görüntülenme": first_present(group.get("1g görüntülenme", pd.Series(dtype=object))),
                    "Sepette": first_present(group.get("Sepette", pd.Series(dtype=object))),
                    "Çok satan sıra": first_present(group.get("Çok satan sıra", pd.Series(dtype=object))),
                    "Sinyal": first_present(group.get("Sinyal", pd.Series(dtype=object))),
                }
            )
        summary_rows.append(summary_row)

    result = pd.DataFrame(summary_rows)
    if "En yüksek stok" in result.columns:
        result = result.sort_values(["Fırsat satırı var", "En yüksek stok"], ascending=[False, True], na_position="last")
    return result


def display_product_links(df):
    if df.empty or "Link" not in df.columns or "Ürün" not in df.columns:
        return df

    display_df = df.copy()
    display_df["Ürün"] = display_df["Ürün"].astype(str)
    display_df["Ürün linki"] = display_df["Link"]
    preferred_columns = []
    for column in display_df.columns:
        if column == "Link":
            continue
        if column == "Ürün":
            preferred_columns.append(column)
            preferred_columns.append("Ürün linki")
            continue
        if column != "Ürün linki":
            preferred_columns.append(column)
    return display_df[preferred_columns]


def product_link_column_config():
    return {
        "Ürün linki": st.column_config.LinkColumn(
            "Aç",
            display_text="Trendyol",
        )
    }


def vat_portion(gross_amount, vat_rate):
    amount = pd.to_numeric(gross_amount, errors="coerce")
    rate = pd.to_numeric(vat_rate, errors="coerce")
    if pd.isna(amount) or pd.isna(rate) or amount <= 0 or rate <= 0:
        return 0.0
    return float(amount) - (float(amount) / (1 + float(rate) / 100))


def calculate_profit(
    sale_price,
    purchase_price,
    commission_rate,
    vat_rate,
    cargo_fee,
    cargo_paid_by_seller,
    service_fee,
    marketing_fee,
    packaging_fee,
    other_fee,
    include_vat_payable,
):
    sale_price = float(sale_price or 0)
    purchase_price = float(purchase_price or 0)
    commission_rate = float(commission_rate or 0)
    vat_rate = float(vat_rate or 0)
    cargo_fee = float(cargo_fee or 0) if cargo_paid_by_seller else 0.0
    service_fee = float(service_fee or 0)
    marketing_fee = float(marketing_fee or 0)
    packaging_fee = float(packaging_fee or 0)
    other_fee = float(other_fee or 0)

    commission = sale_price * commission_rate / 100
    sale_vat = vat_portion(sale_price, vat_rate)
    net_sale_price = sale_price - sale_vat
    stopaj = net_sale_price * TRENDYOL_STOPAJ_RATE / 100
    gross_expenses = {
        "Ürün alış": purchase_price,
        "Komisyon": commission,
        "Kargo": cargo_fee,
        "Hizmet bedeli": service_fee,
        "Pazarlama gideri": marketing_fee,
        "Stopaj": stopaj,
        "Paketleme": packaging_fee,
        "Diğer gider": other_fee,
    }

    deductible_vat = sum(
        vat_portion(value, vat_rate)
        for key, value in gross_expenses.items()
        if key not in ["Stopaj", "Paketleme"]
    )
    payable_vat = sale_vat - deductible_vat
    vat_cash_out = payable_vat if include_vat_payable else 0.0
    total_expense = sum(gross_expenses.values()) + vat_cash_out
    profit = sale_price - total_expense
    profit_margin = (profit / sale_price * 100) if sale_price else 0.0
    roi = (profit / purchase_price * 100) if purchase_price else 0.0

    return {
        "Satış fiyatı": sale_price,
        "Toplam gider": total_expense,
        "Kâr": profit,
        "Kâr oranı": profit_margin,
        "Yatırım geri dönüşü": roi,
        "Komisyon": commission,
        "Stopaj": stopaj,
        "Stopaj oranı": TRENDYOL_STOPAJ_RATE,
        "Satıştan oluşan KDV": sale_vat,
        "Giderlerden düşülecek KDV": deductible_vat,
        "Ödenecek KDV": payable_vat,
        **gross_expenses,
    }


def target_sale_price(base_args, target_profit_rate):
    target_profit_rate = float(target_profit_rate or 0)
    low = 0.01
    high = 1000000.0
    for _ in range(80):
        mid = (low + high) / 2
        result = calculate_profit(sale_price=mid, **base_args)
        margin = result["Kâr oranı"]
        if margin < target_profit_rate:
            low = mid
        else:
            high = mid
    return high


def configurable_table(df, key_prefix, default_columns=None, use_expander=True):
    if df.empty:
        return df

    filtered_df = df.copy()
    available_columns = list(filtered_df.columns)
    visible_options = [column for column in available_columns if column != "Link"]
    default_selection = [
        column
        for column in (default_columns or visible_options)
        if column in visible_options
    ] or visible_options

    controls_area = st.expander("Tablo filtreleri ve kolonlar", expanded=True) if use_expander else st.container()
    with controls_area:
        search_col, numeric_col, sort_col = st.columns([1.2, 1, 1])

        with search_col:
            search_text = st.text_input(
                "Tabloda ara",
                placeholder="Ürün, satıcı, marka...",
                key=f"{key_prefix}_search",
            )

        numeric_columns = [
            column
            for column in available_columns
            if pd.to_numeric(filtered_df[column], errors="coerce").notna().any()
        ]
        with numeric_col:
            selected_numeric_column = st.selectbox(
                "Sayısal filtre",
                options=["Yok"] + numeric_columns,
                key=f"{key_prefix}_numeric_column",
            )

        with sort_col:
            selected_sort_column = st.selectbox(
                "Sırala",
                options=["Yok"] + visible_options,
                key=f"{key_prefix}_sort_column",
            )

        if search_text.strip():
            search_pattern = re.escape(search_text.strip())
            search_mask = filtered_df.astype(str).apply(
                lambda column: column.str.contains(search_pattern, case=False, na=False),
                axis=0,
            ).any(axis=1)
            filtered_df = filtered_df[search_mask]

        if selected_numeric_column != "Yok":
            numeric_series = pd.to_numeric(filtered_df[selected_numeric_column], errors="coerce")
            if numeric_series.notna().any():
                min_value = int(numeric_series.min())
                max_value = int(numeric_series.max())
                range_col_a, range_col_b = st.columns(2)
                with range_col_a:
                    filter_min = st.number_input(
                        "Min",
                        value=min_value,
                        key=f"{key_prefix}_filter_min",
                    )
                with range_col_b:
                    filter_max = st.number_input(
                        "Max",
                        value=max_value,
                        key=f"{key_prefix}_filter_max",
                    )
                filtered_df = filtered_df[
                    numeric_series.ge(filter_min) & numeric_series.le(filter_max)
                ]

        if selected_sort_column != "Yok" and selected_sort_column in filtered_df.columns:
            ascending = st.checkbox(
                "Küçükten büyüğe sırala",
                value=True,
                key=f"{key_prefix}_sort_ascending",
            )
            sort_values = pd.to_numeric(filtered_df[selected_sort_column], errors="coerce")
            if sort_values.notna().any():
                filtered_df = filtered_df.assign(_sort_values=sort_values).sort_values(
                    "_sort_values",
                    ascending=ascending,
                    na_position="last",
                ).drop(columns=["_sort_values"])
            else:
                filtered_df = filtered_df.sort_values(
                    selected_sort_column,
                    ascending=ascending,
                    na_position="last",
                )

        selected_columns = st.multiselect(
            "Kolon sırası / gösterilecek kolonlar",
            options=visible_options,
            default=default_selection,
            key=f"{key_prefix}_columns",
            help="Kolonları seçtiğin sıra ile gösterir. Sırayı değiştirmek için seçimi temizleyip istediğin sırayla yeniden seçebilirsin.",
        )

    selected_columns = selected_columns or visible_options
    output_columns = [column for column in selected_columns if column in filtered_df.columns]
    if "Ürün" in output_columns and "Link" in filtered_df.columns:
        output_columns.append("Link")
    return filtered_df[output_columns]


st.title("Trendyol Fırsat Radarı")
st.caption("Kategori seç, çok satan ürünleri tara, 3 günlük satış adedi ile satıcı stoklarını karşılaştır.")

radar_tab, manual_tab, brand_stock_tab, profit_tab, single_tab = st.tabs(
    ["Fırsat radarı", "Manuel ürün özeti", "Marka ve stok", "Kâr hesabı", "Tek ürün stok okuyucu"]
)

with radar_tab:
    controls, sales_panel = st.columns([1, 1])

    with controls:
        category_names = list(TRENDYOL_CATEGORIES.keys()) + ["Özel kategori linki"]
        selected_category = st.selectbox("Trendyol kategorisi", category_names, index=9)
        custom_category_url = ""
        if selected_category == "Özel kategori linki":
            custom_category_url = st.text_input(
                "Kategori linki",
                placeholder="https://www.trendyol.com/saat-aksesuar-x-c124",
            )
        category_url = custom_category_url.strip() or TRENDYOL_CATEGORIES.get(selected_category)

        selected_listing_sort = st.selectbox(
            "Liste türü",
            list(LISTING_SORT_OPTIONS.keys()),
            index=0,
        )
        pages = st.slider("Taranacak sayfa", min_value=1, max_value=10, value=2)
        product_limit = st.slider("Kontrol edilecek ürün", min_value=5, max_value=100, value=30, step=5)
        seller_filter = st.text_input("Satıcı filtresi", placeholder="Örn. Saat & Saat")
        brand_suggestions = CATEGORY_BRANDS.get(selected_category, [])
        if st.button("Kategori markalarını getir", use_container_width=True):
            if not category_url:
                st.warning("Önce kategori seç veya özel kategori linki gir.")
            else:
                with st.spinner("Markalar çekiliyor..."):
                    discovered_brands = discover_category_brands(category_url)
                if discovered_brands:
                    st.session_state[f"brands:{category_url}"] = discovered_brands
                    st.success(f"{len(discovered_brands)} marka bulundu.")
                else:
                    st.warning("Bu kategori sayfasından marka çıkarılamadı.")
        discovered_key = f"brands:{category_url}"
        if discovered_key in st.session_state:
            brand_suggestions = sorted(
                set(brand_suggestions).union(st.session_state[discovered_key]),
                key=str.casefold,
            )
        selected_brands = st.multiselect("Marka filtresi", options=brand_suggestions)
        custom_brand_filter = st.text_input("Ek marka filtresi", placeholder="Örn. Guess, Casio")
        skip_without_sales = st.checkbox("3 günlük satış verisi olmayan ürünleri fırsat kontrolüne alma", value=True)

    with sales_panel:
        sales_source = st.radio(
            "Satış verisi kaynağı",
            options=["Trendyol ibareleri", "CSV / metin", "Nekadarsatti otomatik"],
            horizontal=True,
        )
        uploaded_file = None
        pasted_sales = ""
        nks_limit = NEKADARSATTI_QUERY_LIMIT
        nks_delay = 2
        max_stock = 150
        min_sales_3d = 100
        min_views_1d = 2000
        min_basket = 1000
        min_favorite = 10000
        max_best_rank = 20
        use_sales_signal = True
        use_views_signal = True
        use_basket_signal = True
        use_favorite_signal = True
        use_rank_signal = True

        if sales_source == "Trendyol ibareleri":
            max_stock = st.number_input("Maksimum stok", min_value=1, max_value=10000, value=150, step=10)
            st.caption("Talep sinyallerinden istediklerini kapatabilirsin.")
            sales_toggle_col, sales_value_col = st.columns([0.45, 1])
            with sales_toggle_col:
                use_sales_signal = st.checkbox("3g satış", value=True, key="use_sales_signal")
            with sales_value_col:
                min_sales_3d = st.number_input(
                    "Min. 3 günlük satış ibaresi",
                    min_value=1,
                    max_value=100000,
                    value=100,
                    step=50,
                    disabled=not use_sales_signal,
                )
            views_toggle_col, views_value_col = st.columns([0.45, 1])
            with views_toggle_col:
                use_views_signal = st.checkbox("1g görüntülenme", value=True, key="use_views_signal")
            with views_value_col:
                min_views_1d = st.number_input(
                    "Min. 1 günlük görüntülenme",
                    min_value=1,
                    max_value=1000000,
                    value=2000,
                    step=500,
                    disabled=not use_views_signal,
                )
            basket_toggle_col, basket_value_col = st.columns([0.45, 1])
            with basket_toggle_col:
                use_basket_signal = st.checkbox("Sepette", value=True, key="use_basket_signal")
            with basket_value_col:
                min_basket = st.number_input(
                    "Min. sepette",
                    min_value=1,
                    max_value=1000000,
                    value=1000,
                    step=250,
                    disabled=not use_basket_signal,
                )
            favorite_toggle_col, favorite_value_col = st.columns([0.45, 1])
            with favorite_toggle_col:
                use_favorite_signal = st.checkbox("Favori", value=True, key="use_favorite_signal")
            with favorite_value_col:
                min_favorite = st.number_input(
                    "Min. favori",
                    min_value=1,
                    max_value=1000000,
                    value=10000,
                    step=1000,
                    disabled=not use_favorite_signal,
                )
            rank_toggle_col, rank_value_col = st.columns([0.45, 1])
            with rank_toggle_col:
                use_rank_signal = st.checkbox("Çok satan sıra", value=True, key="use_rank_signal")
            with rank_value_col:
                max_best_rank = st.number_input(
                    "Maks. çok satan sıra",
                    min_value=1,
                    max_value=1000,
                    value=20,
                    step=1,
                    disabled=not use_rank_signal,
                )
            st.info("Fırsat kuralı: stok <= maksimum stok ve açık talep sinyallerinden en az biri eşik üstü.")
        elif sales_source == "CSV / metin":
            uploaded_file = st.file_uploader(
                "Nekadarsatti satış verisi CSV",
                type=["csv", "txt"],
                help="Kolon örnekleri: Ürün ID, Link, 3 günlük satış, sales_3d, adet",
            )
            pasted_sales = st.text_area(
                "Veya satış verisini yapıştır",
                placeholder="https://www.trendyol.com/...-p-123456789 18\n123456790, 7",
                height=132,
            )
        else:
            nks_limit = st.slider(
                "Nekadarsatti sorgu hakkı",
                min_value=1,
                max_value=NEKADARSATTI_QUERY_LIMIT,
                value=5,
            )
            nks_delay = st.slider(
                "Sorgular arası bekleme",
                min_value=0,
                max_value=10,
                value=2,
                help="Aynı IP'den nazik ve düşük tempolu deneme için.",
            )
            st.info(
                "Bu mod seçtiğin ürün sayısı kadar aynı IP'den nekadarsatti sorgusu yapar. "
                "Limit dolarsa hata tablosunda görünür."
            )
        st.caption(
            "CSV/Nekadarsatti modu: stok <= son 3 günlük satış. Trendyol ibareleri modu: stok + talep sinyali."
        )

    run_radar = st.button("Fırsatları tara", type="primary", use_container_width=True)

    if run_radar:
        try:
            if not category_url:
                raise ValueError("Kategori linki boş olamaz.")

            with st.status("Çok satan ürünler çekiliyor...", expanded=True) as status:
                products = discover_category_products(
                    category_url,
                    pages,
                    product_limit,
                    LISTING_SORT_OPTIONS[selected_listing_sort],
                )
                if not products:
                    raise RuntimeError("Kategori sayfasından ürün linki çıkarılamadı.")
                st.write(f"{len(products)} ürün bulundu.")

                sales_rows = []
                sales_errors = []
                if sales_source == "Trendyol ibareleri":
                    active_signal_count = sum(
                        [
                            use_sales_signal,
                            use_views_signal,
                            use_basket_signal,
                            use_favorite_signal,
                            use_rank_signal,
                        ]
                    )
                    if active_signal_count == 0:
                        raise ValueError("En az bir talep sinyali açık olmalı.")
                    progress = st.progress(0, text="Trendyol ibareleri ve stoklar kontrol ediliyor")
                    opportunities, checked, errors = find_signal_opportunities(
                        products,
                        seller_filter.strip(),
                        selected_brands,
                        custom_brand_filter,
                        max_stock,
                        min_sales_3d if use_sales_signal else None,
                        min_views_1d if use_views_signal else None,
                        min_basket if use_basket_signal else None,
                        min_favorite if use_favorite_signal else None,
                        max_best_rank if use_rank_signal else None,
                        progress,
                    )
                elif sales_source == "Nekadarsatti otomatik":
                    sales_map, sales_rows, sales_errors = fetch_nekadarsatti_sales_map(
                        products,
                        nks_limit,
                        nks_delay,
                        st,
                    )
                else:
                    sales_map = load_sales_map(uploaded_file, pasted_sales)

                if sales_source != "Trendyol ibareleri":
                    if not sales_map and skip_without_sales:
                        raise ValueError("Satış verisi alınamadı. CSV/metin ekle veya Nekadarsatti limit/hata durumunu kontrol et.")

                    progress = st.progress(0, text="Stoklar kontrol ediliyor")
                    opportunities, checked, errors = find_opportunities(
                        products,
                        sales_map,
                        seller_filter.strip(),
                        skip_without_sales,
                        progress,
                    )
                    errors.extend(sales_errors)
                status.update(label="Tarama tamamlandı.", state="complete")

            st.session_state["radar_result"] = {
                "products": products,
                "sales_rows": sales_rows,
                "opportunities": opportunities,
                "checked": checked,
                "errors": errors,
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as exc:
            st.error(str(exc))

    if "radar_result" in st.session_state:
        result = st.session_state["radar_result"]
        opportunities_df = pd.DataFrame(result["opportunities"])
        checked_df = pd.DataFrame(result["checked"])
        sales_df = pd.DataFrame(result.get("sales_rows", []))
        errors_df = pd.DataFrame(result["errors"])

        st.divider()
        metric_cols = st.columns(4)
        metric_cols[0].metric("Bulunan ürün", len(result["products"]))
        metric_cols[1].metric("Kontrol edilen satıcı/varyant", len(checked_df))
        metric_cols[2].metric("Fırsat", len(opportunities_df))
        metric_cols[3].metric("Hata", len(errors_df))
        st.caption(f"Son kontrol: {result['checked_at']}")

        result_tabs = st.tabs(["Fırsatlar", "Tüm kontrol sonuçları", "Nekadarsatti", "Hatalar"])

        with result_tabs[0]:
            st.subheader("Fırsat listesi")
            if opportunities_df.empty:
                st.info("Bu kriterlerle fırsat ürünü bulunamadı.")
            else:
                st.dataframe(
                    display_product_links(opportunities_df),
                    use_container_width=True,
                    hide_index=True,
                    column_config=product_link_column_config(),
                )
                st.download_button(
                    "Fırsat listesini CSV indir",
                    data=dataframe_download(opportunities_df),
                    file_name="trendyol_firsat_listesi.csv",
                    mime="text/csv",
                )

        with result_tabs[1]:
            if checked_df.empty:
                st.info("Kontrol sonucu yok.")
            else:
                st.dataframe(checked_df, use_container_width=True, hide_index=True)

        with result_tabs[2]:
            if sales_df.empty:
                st.info("Otomatik Nekadarsatti sonucu yok.")
            else:
                st.dataframe(sales_df, use_container_width=True, hide_index=True)

        with result_tabs[3]:
            if errors_df.empty:
                st.success("Hata yok.")
            else:
                st.dataframe(errors_df, use_container_width=True, hide_index=True)

with manual_tab:
    st.subheader("Ürün bazlı manuel kontrol")
    st.caption("Fırsat taramasından gelen sonuçları ürün başına tek satıra indirir. Aynı ürünün satıcı stokları ayrı ayrı satır oluşturmaz.")

    if "radar_result" not in st.session_state:
        st.info("Önce Fırsat radarı sekmesinde tarama yap. Sonuçlar burada ürün bazlı özetlenecek.")
    else:
        result = st.session_state["radar_result"]
        checked_df = pd.DataFrame(result["checked"])
        product_summary_df = product_summary_rows(checked_df, include_signal_columns=False)

        metric_cols = st.columns(4)
        metric_cols[0].metric("Ürün", len(product_summary_df))
        metric_cols[1].metric("Fırsat işaretli", int((product_summary_df.get("Fırsat satırı var", pd.Series(dtype=object)) == "Evet").sum()) if not product_summary_df.empty else 0)
        metric_cols[2].metric("Kontrol edilen satır", len(checked_df))
        metric_cols[3].metric("Son kontrol", result["checked_at"])

        if product_summary_df.empty:
            st.info("Ürün özeti yok.")
        else:
            st.dataframe(
                display_product_links(product_summary_df),
                use_container_width=True,
                hide_index=True,
                column_config=product_link_column_config(),
            )
            st.download_button(
                "Ürün özetlerini CSV indir",
                data=dataframe_download(product_summary_df),
                file_name="trendyol_urun_ozetleri.csv",
                mime="text/csv",
            )

with brand_stock_tab:
    st.subheader("Marka ve stok")
    st.caption("Seçtiğin markanın Trendyol marka sayfasını veya arama sonuçlarını tarar ve ürün max stoku belirlediğin eşiğin altında kalanları listeler.")

    brand_name_col, max_stock_col, product_count_col = st.columns([1, 1, 1])

    with brand_name_col:
        brand_stock_brands = st.multiselect(
            "Marka",
            options=sorted(BRAND_STOCK_BRANDS.keys(), key=str.casefold),
            default=["Guess"] if "Guess" in BRAND_STOCK_BRANDS else None,
            key="brand_stock_brands",
        )

    with max_stock_col:
        brand_stock_max = st.number_input(
            "Maksimum ürün stoku",
            min_value=1,
            max_value=100000,
            value=150,
            step=10,
            key="brand_stock_max_stock",
        )

    with product_count_col:
        brand_stock_product_limit = st.number_input(
            "Kontrol edilecek ürün",
            min_value=1,
            max_value=10000,
            value=300,
            step=100,
            key="brand_stock_product_limit",
        )

    brand_batch_size = st.slider(
        "Tek seferde kontrol edilecek ürün",
        min_value=50,
        max_value=500,
        value=200,
        step=50,
        help="Online sitede kapanma yaşamamak için büyük taramaları parça parça çalıştırır.",
    )
    brand_parallel_workers = st.slider(
        "Hız",
        min_value=1,
        max_value=12,
        value=8,
        step=1,
        help="Aynı anda kaç ürün sayfası kontrol edilsin. Bağlantı zayıfsa düşür.",
    )

    active_result = st.session_state.get("brand_stock_result")
    scan_running = bool(active_result and active_result.get("running") and not active_result.get("complete"))

    button_col_a, button_col_b = st.columns([1, 0.35])
    with button_col_a:
        run_brand_stock = st.button(
            "Marka stoklarını başlat / devam et",
            type="primary",
            use_container_width=True,
            disabled=scan_running,
        )
    with button_col_b:
        stop_brand_stock = st.button("Durdur", use_container_width=True, disabled=not scan_running)

    reset_brand_stock = st.button("Sonucu sıfırla", use_container_width=True)

    if reset_brand_stock:
        st.session_state.pop("brand_stock_result", None)
        st.rerun()

    if stop_brand_stock and active_result:
        active_result["running"] = False
        st.session_state["brand_stock_result"] = active_result
        st.rerun()

    if run_brand_stock and active_result and not active_result.get("complete"):
        active_result["running"] = True
        st.session_state["brand_stock_result"] = active_result
        st.rerun()

    if run_brand_stock or scan_running:
        try:
            selected_brand_names = [brand.strip() for brand in brand_stock_brands if brand.strip()]
            if not selected_brand_names:
                raise ValueError("Önce en az bir marka seç.")

            result = st.session_state.get("brand_stock_result")
            result_signature = {
                "brand": ", ".join(selected_brand_names),
                "max_stock": int(brand_stock_max),
                "product_limit": int(brand_stock_product_limit),
            }
            if (
                not result
                or result.get("brand") != result_signature["brand"]
                or int(result.get("max_stock", 0)) != result_signature["max_stock"]
                or int(result.get("product_limit", 0)) != result_signature["product_limit"]
            ):
                with st.status("Marka ürünleri çekiliyor...", expanded=True) as status:
                    brand_stock_pages = max(
                        1,
                        int((brand_stock_product_limit + BRAND_STOCK_PRODUCTS_PER_PAGE - 1) // BRAND_STOCK_PRODUCTS_PER_PAGE),
                    )
                    products = []
                    per_brand_limit = int(brand_stock_product_limit)
                    for brand_name in selected_brand_names:
                        brand_url = BRAND_STOCK_BRANDS.get(brand_name)
                        st.write(f"{brand_name}: ürünler çekiliyor...")
                        if brand_url:
                            products.extend(
                                discover_category_products(
                                    brand_url,
                                    brand_stock_pages,
                                    per_brand_limit,
                                    None,
                                )
                            )
                        else:
                            products.extend(
                                discover_search_products(
                                    brand_name,
                                    brand_stock_pages,
                                    per_brand_limit,
                                )
                            )
                    products = unique_products(products)[: int(brand_stock_product_limit)]
                    if not products:
                        raise RuntimeError("Marka sayfasından ürün linki çıkarılamadı.")
                    st.write(f"{len(products)} ürün bulundu.")
                    status.update(label="Ürün listesi hazır.", state="complete")
                result = {
                    "products": products,
                    "checked": [],
                    "errors": [],
                    "stats": {},
                    "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "max_stock": result_signature["max_stock"],
                    "brand": result_signature["brand"],
                    "product_limit": result_signature["product_limit"],
                    "next_index": 0,
                    "complete": False,
                    "running": True,
                }
            else:
                result["running"] = True

            products = result["products"]
            start_index = int(result.get("next_index", 0))
            if start_index >= len(products):
                result["complete"] = True
                result["running"] = False
                st.session_state["brand_stock_result"] = result
                st.success("Bu tarama zaten tamamlanmış.")
            else:
                progress = st.progress(0, text="Marka ve stoklar kontrol ediliyor")
                live_container = st.empty()
                checked, errors, stats, next_index = find_brand_stock_products_parallel(
                    products,
                    "",
                    selected_brand_names,
                    "",
                    brand_stock_max,
                    progress,
                    live_container,
                    existing_checked=result.get("checked", []),
                    start_index=start_index,
                    batch_size=int(brand_batch_size),
                    workers=int(brand_parallel_workers),
                )
                result["checked"].extend(checked)
                result["errors"].extend(errors)
                result["stats"] = merge_stats(result.get("stats"), stats)
                result["next_index"] = next_index
                result["checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result["complete"] = next_index >= len(products)
                result["running"] = not result["complete"]
                st.session_state["brand_stock_result"] = result
                if result["complete"]:
                    st.success("Marka stok taraması tamamlandı.")
                else:
                    st.info(f"{next_index}/{len(products)} ürün kontrol edildi. Otomatik devam ediyor...")
                    time.sleep(0.5)
                    st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if "brand_stock_result" in st.session_state:
        result = st.session_state["brand_stock_result"]
        checked_df = pd.DataFrame(result["checked"])
        errors_df = pd.DataFrame(result["errors"])
        product_summary_df = product_summary_rows(checked_df)

        st.divider()
        metric_cols = st.columns(4)
        metric_cols[0].metric("Taranan ürün", len(result["products"]))
        metric_cols[1].metric("Eşleşen ürün", len(product_summary_df))
        metric_cols[2].metric("Satıcı/varyant satırı", len(checked_df))
        metric_cols[3].metric("Hata", len(errors_df))
        stats = result.get("stats", {})
        st.caption(
            f"Son kontrol: {result['checked_at']} | Marka: {result.get('brand', '-')} | "
            f"Maksimum ürün stoku: {result['max_stock']} | Ürün limiti: {result.get('product_limit', '-')}"
        )
        next_index = int(result.get("next_index", len(result["products"]) if result.get("complete") else 0))
        total_products = len(result["products"])
        progress_ratio = next_index / max(total_products, 1)
        st.progress(progress_ratio, text=f"İlerleme: {next_index}/{total_products} ürün kontrol edildi")
        if result.get("running") and not result.get("complete"):
            st.info("Tarama otomatik devam ediyor. İstersen Durdur butonuyla ara verebilirsin.")
        elif not result.get("complete"):
            st.info("Tarama duraklatıldı. Devam etmek için başlat/devam et butonuna bas.")
        if stats:
            st.caption(
                f"Kontrol özeti: marka eşleşen {stats.get('Marka eşleşti', 0)} ürün, "
                f"stok okunabilen {stats.get('Stok okunabildi', 0)} ürün, "
                f"stok eşiği üstünde kalan {stats.get('Stok eşiği üstü', 0)} ürün."
            )

        if product_summary_df.empty:
            st.info("Bu marka ve maksimum stok eşiğiyle ürün bulunamadı.")
        else:
            default_brand_stock_columns = [
                "Ürün ID",
                "Ürün",
                "Marka",
                "En yüksek stok satıcısı",
                "En yüksek stok",
                "Toplam stok",
                "Satıcı stokları",
                "Favori",
                "Yorum",
                "Değerlendirme",
            ]
            filtered_summary_df = configurable_table(
                product_summary_df,
                "brand_stock_summary",
                default_brand_stock_columns,
            )
            st.dataframe(
                display_product_links(filtered_summary_df),
                use_container_width=True,
                hide_index=True,
                column_config=product_link_column_config(),
            )
            st.download_button(
                "Marka stok listesini CSV indir",
                data=dataframe_download(filtered_summary_df),
                file_name="trendyol_marka_stok_listesi.csv",
                mime="text/csv",
            )

        with st.expander("Satıcı/varyant detayları"):
            if checked_df.empty:
                st.info("Detay satırı yok.")
            else:
                filtered_checked_df = configurable_table(
                    checked_df,
                    "brand_stock_details",
                    [
                        "Ürün ID",
                        "Ürün",
                        "Marka",
                        "Satıcı",
                        "Varyant",
                        "Stok",
                        "Toplam stok",
                        "Fiyat",
                        "Favori",
                        "Yorum",
                        "Değerlendirme",
                    ],
                    use_expander=False,
                )
                st.dataframe(
                    display_product_links(filtered_checked_df),
                    use_container_width=True,
                    hide_index=True,
                    column_config=product_link_column_config(),
                )

        with st.expander("Hatalar"):
            if errors_df.empty:
                st.success("Hata yok.")
            else:
                st.dataframe(
                    display_product_links(errors_df),
                    use_container_width=True,
                    hide_index=True,
                    column_config=product_link_column_config(),
                )

with profit_tab:
    st.subheader("Kâr hesabı")
    st.caption("Satış, alış, komisyon, KDV, kargo ve ek giderleri girerek Trendyol net kârını hesaplar.")

    price_col, fee_col = st.columns([1, 1])

    with price_col:
        selected_commission_category = st.selectbox(
            "Kategori / komisyon preset",
            options=list(COMMISSION_PRESETS.keys()),
            index=list(COMMISSION_PRESETS.keys()).index("Saat"),
        )
        preset_commission = COMMISSION_PRESETS[selected_commission_category]
        sale_price = st.number_input(
            "Ürün satış fiyatı (KDV dahil)",
            min_value=0.0,
            value=1000.0,
            step=10.0,
            format="%.2f",
        )
        purchase_price = st.number_input(
            "Ürün alış fiyatı (KDV dahil)",
            min_value=0.0,
            value=600.0,
            step=10.0,
            format="%.2f",
        )
        commission_rate = st.number_input(
            "Komisyon %",
            min_value=0.0,
            max_value=100.0,
            value=float(preset_commission if preset_commission is not None else 20.0),
            step=0.1,
            format="%.2f",
        )
        vat_rate = st.number_input(
            "KDV %",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=1.0,
            format="%.2f",
        )
        include_vat_payable = st.checkbox("Ödenecek KDV'yi kârdan düş", value=True)

    with fee_col:
        cargo_paid_by_seller = st.checkbox("Kargo satıcıya ait", value=True)
        cargo_fee = st.number_input(
            "Kargo ücreti (KDV dahil)",
            min_value=0.0,
            value=85.0,
            step=5.0,
            format="%.2f",
            disabled=not cargo_paid_by_seller,
        )
        service_fee_type = st.radio(
            "Platform hizmet bedeli",
            options=["Standart", "Bugün Kargoda"],
            horizontal=True,
        )
        service_fee = (
            TRENDYOL_SAME_DAY_SERVICE_FEE
            if service_fee_type == "Bugün Kargoda"
            else TRENDYOL_PLATFORM_SERVICE_FEE
        )
        st.caption(
            f"Hizmet bedeli: {service_fee:,.2f} TL | "
            f"Stopaj: KDV hariç satış x %{TRENDYOL_STOPAJ_RATE:g}"
        )
        marketing_fee = st.number_input(
            "Pazarlama / reklam gideri (KDV dahil)",
            min_value=0.0,
            value=0.0,
            step=5.0,
            format="%.2f",
        )
        packaging_fee = st.number_input(
            "Paketleme gideri",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
        )
        other_fee = st.number_input(
            "Diğer gider (KDV dahil)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
        )

    base_profit_args = {
        "purchase_price": purchase_price,
        "commission_rate": commission_rate,
        "vat_rate": vat_rate,
        "cargo_fee": cargo_fee,
        "cargo_paid_by_seller": cargo_paid_by_seller,
        "service_fee": service_fee,
        "marketing_fee": marketing_fee,
        "packaging_fee": packaging_fee,
        "other_fee": other_fee,
        "include_vat_payable": include_vat_payable,
    }
    profit_result = calculate_profit(sale_price=sale_price, **base_profit_args)

    st.divider()
    metric_cols = st.columns(4)
    metric_cols[0].metric("Net kâr", f"{profit_result['Kâr']:,.2f} TL")
    metric_cols[1].metric("Kâr oranı", f"%{profit_result['Kâr oranı']:,.2f}")
    metric_cols[2].metric("Yatırım geri dönüşü", f"%{profit_result['Yatırım geri dönüşü']:,.2f}")
    metric_cols[3].metric("Toplam gider", f"{profit_result['Toplam gider']:,.2f} TL")

    target_col, target_result_col = st.columns([1, 1])
    with target_col:
        target_profit_rate = st.number_input(
            "Hedef kâr oranı için gereken satış fiyatı",
            min_value=0.0,
            max_value=95.0,
            value=20.0,
            step=1.0,
            format="%.2f",
        )
    with target_result_col:
        target_price = target_sale_price(base_profit_args, target_profit_rate)
        st.metric("Gerekli satış fiyatı", f"{target_price:,.2f} TL")

    detail_rows = [
        ("Satış fiyatı", profit_result["Satış fiyatı"]),
        ("Ürün alış", profit_result["Ürün alış"]),
        ("Komisyon", profit_result["Komisyon"]),
        ("Kargo", profit_result["Kargo"]),
        ("Hizmet bedeli", profit_result["Hizmet bedeli"]),
        ("Pazarlama gideri", profit_result["Pazarlama gideri"]),
        ("Stopaj", profit_result["Stopaj"]),
        ("Paketleme", profit_result["Paketleme"]),
        ("Diğer gider", profit_result["Diğer gider"]),
        ("Satıştan oluşan KDV", profit_result["Satıştan oluşan KDV"]),
        ("Giderlerden düşülecek KDV", profit_result["Giderlerden düşülecek KDV"]),
        ("Ödenecek KDV", profit_result["Ödenecek KDV"]),
        ("Toplam gider", profit_result["Toplam gider"]),
        ("Net kâr", profit_result["Kâr"]),
    ]
    detail_df = pd.DataFrame(detail_rows, columns=["Kalem", "Tutar"])
    detail_df["Tutar"] = detail_df["Tutar"].map(lambda value: f"{value:,.2f} TL")
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    st.caption(
        "Komisyon presetleri yaklaşık başlangıç değeridir. Kesin oranı ürün alt kategorisine göre "
        "Trendyol Satıcı Paneli'nden kontrol edip manuel komisyon alanına yaz."
    )

with single_tab:
    left_col, right_col = st.columns([1.2, 0.8])

    with left_col:
        product_url = st.text_input(
            "Trendyol ürün linki",
            placeholder="https://www.trendyol.com/marka/urun-adi-p-123456789",
        )
        source_text = st.text_area(
            "Kaynak metin (opsiyonel)",
            placeholder='window["__envoy_product-info__PROPS"]={...}',
            height=180,
        )

    with right_col:
        st.markdown("#### Okuma modu")
        mode = st.radio(
            "Veri kaynağı",
            options=["Linkten oku", "Kaynak metinden oku"],
            label_visibility="collapsed",
        )
        show_raw = st.checkbox("Ham quantity eşleşmelerini göster", value=True)
        run_button = st.button("Stokları getir", type="primary", use_container_width=True)

    if run_button:
        try:
            if mode == "Linkten oku":
                if not product_url.strip():
                    raise ValueError("Önce Trendyol ürün linkini yapıştır.")
                source = fetch_page(validate_trendyol_url(product_url))
            else:
                if not source_text.strip():
                    raise ValueError("Önce inspect içinden aldığın kaynak metni yapıştır.")
                source = source_text

            summary, rows, raw_rows = analyze_source(source)
            st.session_state["single_result"] = {
                "summary": summary,
                "rows": rows,
                "raw_rows": raw_rows,
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as exc:
            st.session_state.pop("single_result", None)
            st.error(str(exc))

    if "single_result" in st.session_state:
        result = st.session_state["single_result"]
        summary = result["summary"]
        stock_df = pd.DataFrame(result["rows"])
        raw_df = pd.DataFrame(result["raw_rows"])

        st.divider()
        top_left, top_right = st.columns([2, 1])
        with top_left:
            st.subheader(summary["Ürün"])
            st.write(f"Marka: {summary.get('Marka') or '-'}")
            st.caption(f"Son kontrol: {result['checked_at']}")
        with top_right:
            quantities = pd.to_numeric(stock_df["Quantity"], errors="coerce").dropna()
            st.metric("Satıcı/varyant", len(stock_df))
            st.metric("Toplam quantity", int(quantities.sum()) if not quantities.empty else 0)
            st.metric("En yüksek quantity", int(quantities.max()) if not quantities.empty else 0)

        st.dataframe(stock_df, use_container_width=True, hide_index=True)

        if show_raw:
            st.write("Ham quantity eşleşmeleri")
            if raw_df.empty:
                st.info('Kaynakta `"quantity":123` formatında değer bulunamadı.')
            else:
                st.dataframe(raw_df, use_container_width=True, hide_index=True)

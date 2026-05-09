import csv
import html
import io
import json
import os
import re
import time
from datetime import datetime
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
NEKADARSATTI_API_URL = "https://nekadarsatti.com/api/sales-number"
NEKADARSATTI_PUBLIC_API_KEY = "aJ9cgcACBCY1d3dWmJhWW8n2v2GhgP"
NEKADARSATTI_QUERY_LIMIT = 30

LISTING_SORT_OPTIONS = {
    "En çok satan": "BEST_SELLER",
    "En çok ziyaret edilen": "MOST_VISITED",
    "En çok değerlendirilen": "MOST_RATED",
    "En çok favorilenen": "MOST_FAVOURITE",
}


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

    if st.session_state.get("authenticated"):
        return True

    st.title("Trendyol Fırsat Radarı")
    st.caption("Devam etmek için giriş yap.")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş yap", type="primary"):
        if password == app_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Şifre hatalı.")
    return False


if not require_password():
    st.stop()


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
    query["sst"] = sort_value
    query["pi"] = str(page_no)
    return urlunparse(parsed._replace(query=urlencode(query)))


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

    for page_no in range(1, pages + 1):
        source = request_page(with_category_query(category_url, page_no, sort_value))
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

    if pd.notna(sales_3d) and int(sales_3d) >= min_sales_3d:
        hits.append(f"3g satış {int(sales_3d)}+")
    if pd.notna(views_1d) and int(views_1d) >= min_views_1d:
        hits.append(f"1g görüntülenme {int(views_1d)}+")
    if pd.notna(basket) and int(basket) >= min_basket:
        hits.append(f"sepette {int(basket)}+")
    if pd.notna(favorite) and int(favorite) >= min_favorite:
        hits.append(f"favori {int(favorite)}+")
    if pd.notna(best_rank) and int(best_rank) <= max_best_rank:
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
            signal = analyze_trendyol_signals(source)
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
):
    checked_rows = []
    errors = []

    for index, product in enumerate(products, start=1):
        progress.progress(index / max(len(products), 1), text=f"{index}/{len(products)} marka/stok kontrol ediliyor")
        product_id = str(product["Ürün ID"])

        try:
            source = fetch_page(product["Link"])
            summary, rows, _ = analyze_source(source)
            signal = analyze_trendyol_signals(source)
        except Exception as exc:
            errors.append({"Ürün ID": product_id, "Ürün": product["Ürün"], "Hata": str(exc), "Link": product["Link"]})
            continue

        if not brand_matches(summary.get("Marka"), selected_brands, custom_brand_filter):
            continue

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
            continue

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

    progress.empty()
    return checked_rows, errors


def dataframe_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def first_present(series):
    for value in series:
        if pd.notna(value) and value not in [None, ""]:
            return value
    return None


def product_summary_rows(checked_df):
    if checked_df.empty or "Ürün ID" not in checked_df.columns:
        return pd.DataFrame()

    summary_rows = []
    for product_id, group in checked_df.groupby("Ürün ID", dropna=False):
        stock_series = pd.to_numeric(group.get("Stok"), errors="coerce")
        stock_rows = group[stock_series.notna()].copy()

        top_seller = None
        top_stock = None
        other_stocks = None
        seller_stock_text = None

        if not stock_rows.empty:
            stock_rows["_stock_numeric"] = pd.to_numeric(stock_rows["Stok"], errors="coerce")
            stock_rows = stock_rows.sort_values("_stock_numeric", ascending=False)
            top_row = stock_rows.iloc[0]
            top_seller = top_row.get("Satıcı")
            top_stock = int(top_row["_stock_numeric"])
            other_values = [str(int(value)) for value in stock_rows["_stock_numeric"].iloc[1:].dropna()]
            other_stocks = "/".join(other_values) if other_values else None
            seller_stock_text = " / ".join(
                f"{row.get('Satıcı')}: {int(row['_stock_numeric'])}"
                for _, row in stock_rows.iterrows()
                if pd.notna(row.get("_stock_numeric"))
            )

        summary_rows.append(
            {
                "Ürün ID": product_id,
                "Ürün": first_present(group.get("Ürün", pd.Series(dtype=object))),
                "Marka": first_present(group.get("Marka", pd.Series(dtype=object))),
                "Liste etiketi": first_present(group.get("Liste etiketi", pd.Series(dtype=object))),
                "En yüksek stok satıcısı": top_seller,
                "En yüksek stok": top_stock,
                "Ürün max stok": first_present(group.get("Ürün max stok", pd.Series(dtype=object))) or top_stock,
                "Max stok satıcısı": first_present(group.get("Max stok satıcısı", pd.Series(dtype=object))) or top_seller,
                "Diğer stoklar": other_stocks,
                "Satıcı stokları": seller_stock_text,
                "3 günlük satış": first_present(group.get("3 günlük satış", pd.Series(dtype=object))),
                "3g satış ibaresi": first_present(group.get("3g satış ibaresi", pd.Series(dtype=object))),
                "1g görüntülenme": first_present(group.get("1g görüntülenme", pd.Series(dtype=object))),
                "Sepette": first_present(group.get("Sepette", pd.Series(dtype=object))),
                "Favori": first_present(group.get("Favori", pd.Series(dtype=object))),
                "Yorum": first_present(group.get("Yorum", pd.Series(dtype=object))),
                "Değerlendirme": first_present(group.get("Değerlendirme", pd.Series(dtype=object))),
                "Çok satan sıra": first_present(group.get("Çok satan sıra", pd.Series(dtype=object))),
                "Sinyal": first_present(group.get("Sinyal", pd.Series(dtype=object))),
                "Fırsat satırı var": "Evet" if (group.get("Fırsat", pd.Series(dtype=object)) == "Evet").any() else "Hayır",
                "Link": first_present(group.get("Link", pd.Series(dtype=object))),
            }
        )

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


st.title("Trendyol Fırsat Radarı")
st.caption("Kategori seç, çok satan ürünleri tara, 3 günlük satış adedi ile satıcı stoklarını karşılaştır.")

radar_tab, manual_tab, brand_stock_tab, single_tab = st.tabs(
    ["Fırsat radarı", "Manuel ürün özeti", "Marka ve stok", "Tek ürün stok okuyucu"]
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

        if sales_source == "Trendyol ibareleri":
            max_stock = st.number_input("Maksimum stok", min_value=1, max_value=10000, value=150, step=10)
            min_sales_3d = st.number_input("Min. 3 günlük satış ibaresi", min_value=1, max_value=100000, value=100, step=50)
            min_views_1d = st.number_input("Min. 1 günlük görüntülenme", min_value=1, max_value=1000000, value=2000, step=500)
            min_basket = st.number_input("Min. sepette", min_value=1, max_value=1000000, value=1000, step=250)
            col_a, col_b = st.columns(2)
            with col_a:
                min_favorite = st.number_input("Min. favori", min_value=1, max_value=1000000, value=10000, step=1000)
            with col_b:
                max_best_rank = st.number_input("Maks. çok satan sıra", min_value=1, max_value=1000, value=20, step=1)
            st.info("Fırsat kuralı: stok <= maksimum stok ve talep sinyallerinden en az biri eşik üstü.")
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
                    progress = st.progress(0, text="Trendyol ibareleri ve stoklar kontrol ediliyor")
                    opportunities, checked, errors = find_signal_opportunities(
                        products,
                        seller_filter.strip(),
                        selected_brands,
                        custom_brand_filter,
                        max_stock,
                        min_sales_3d,
                        min_views_1d,
                        min_basket,
                        min_favorite,
                        max_best_rank,
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
        product_summary_df = product_summary_rows(checked_df)

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
    st.caption("Seçtiğin kategori listesindeki ürünleri tarar, sadece seçtiğin markaya ait ve ürün max stoku belirlediğin eşiğin altında olanları listeler.")

    brand_controls, brand_filters = st.columns([1, 1])

    with brand_controls:
        brand_category_names = list(TRENDYOL_CATEGORIES.keys()) + ["Özel kategori linki"]
        brand_selected_category = st.selectbox(
            "Trendyol kategorisi",
            brand_category_names,
            index=30,
            key="brand_stock_category",
        )
        brand_custom_category_url = ""
        if brand_selected_category == "Özel kategori linki":
            brand_custom_category_url = st.text_input(
                "Kategori linki",
                placeholder="https://www.trendyol.com/saat-x-c34",
                key="brand_stock_custom_category_url",
            )
        brand_category_url = brand_custom_category_url.strip() or TRENDYOL_CATEGORIES.get(brand_selected_category)

        brand_listing_sort = st.selectbox(
            "Liste türü",
            list(LISTING_SORT_OPTIONS.keys()),
            index=0,
            key="brand_stock_listing_sort",
        )
        brand_pages = st.slider(
            "Taranacak sayfa",
            min_value=1,
            max_value=20,
            value=3,
            key="brand_stock_pages",
        )
        brand_product_limit = st.slider(
            "Kontrol edilecek ürün",
            min_value=5,
            max_value=300,
            value=60,
            step=5,
            key="brand_stock_product_limit",
        )

    with brand_filters:
        brand_suggestions = CATEGORY_BRANDS.get(brand_selected_category, [])
        if st.button("Kategori markalarını getir", use_container_width=True, key="brand_stock_fetch_brands"):
            if not brand_category_url:
                st.warning("Önce kategori seç veya özel kategori linki gir.")
            else:
                with st.spinner("Markalar çekiliyor..."):
                    discovered_brands = discover_category_brands(brand_category_url)
                if discovered_brands:
                    st.session_state[f"brand_stock_brands:{brand_category_url}"] = discovered_brands
                    st.success(f"{len(discovered_brands)} marka bulundu.")
                else:
                    st.warning("Bu kategori sayfasından marka çıkarılamadı. Markayı ek marka alanına yazabilirsin.")

        discovered_brand_key = f"brand_stock_brands:{brand_category_url}"
        if discovered_brand_key in st.session_state:
            brand_suggestions = sorted(
                set(brand_suggestions).union(st.session_state[discovered_brand_key]),
                key=str.casefold,
            )

        brand_stock_selected_brands = st.multiselect(
            "Marka",
            options=brand_suggestions,
            key="brand_stock_selected_brands",
        )
        brand_stock_custom_brand = st.text_input(
            "Ek marka",
            placeholder="Örn. Guess, Casio",
            key="brand_stock_custom_brand",
        )
        brand_stock_max = st.number_input(
            "Maksimum ürün stoku",
            min_value=1,
            max_value=100000,
            value=150,
            step=10,
            key="brand_stock_max_stock",
        )
        brand_stock_seller_filter = st.text_input(
            "Satıcı filtresi (opsiyonel)",
            placeholder="Örn. Saat & Saat",
            key="brand_stock_seller_filter",
        )

    run_brand_stock = st.button("Marka stoklarını listele", type="primary", use_container_width=True)

    if run_brand_stock:
        try:
            if not brand_category_url:
                raise ValueError("Kategori linki boş olamaz.")
            if not brand_stock_selected_brands and not brand_stock_custom_brand.strip():
                raise ValueError("Önce marka seç veya ek marka alanına marka yaz.")

            with st.status("Kategori ürünleri çekiliyor...", expanded=True) as status:
                products = discover_category_products(
                    brand_category_url,
                    brand_pages,
                    brand_product_limit,
                    LISTING_SORT_OPTIONS[brand_listing_sort],
                )
                if not products:
                    raise RuntimeError("Kategori sayfasından ürün linki çıkarılamadı.")
                st.write(f"{len(products)} ürün bulundu.")

                progress = st.progress(0, text="Marka ve stoklar kontrol ediliyor")
                checked, errors = find_brand_stock_products(
                    products,
                    brand_stock_seller_filter.strip(),
                    brand_stock_selected_brands,
                    brand_stock_custom_brand,
                    brand_stock_max,
                    progress,
                )
                status.update(label="Marka stok taraması tamamlandı.", state="complete")

            st.session_state["brand_stock_result"] = {
                "products": products,
                "checked": checked,
                "errors": errors,
                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "max_stock": brand_stock_max,
            }
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
        st.caption(f"Son kontrol: {result['checked_at']} | Maksimum ürün stoku: {result['max_stock']}")

        if product_summary_df.empty:
            st.info("Bu marka ve maksimum stok eşiğiyle ürün bulunamadı.")
        else:
            st.dataframe(
                display_product_links(product_summary_df),
                use_container_width=True,
                hide_index=True,
                column_config=product_link_column_config(),
            )
            st.download_button(
                "Marka stok listesini CSV indir",
                data=dataframe_download(product_summary_df),
                file_name="trendyol_marka_stok_listesi.csv",
                mime="text/csv",
            )

        with st.expander("Satıcı/varyant detayları"):
            if checked_df.empty:
                st.info("Detay satırı yok.")
            else:
                st.dataframe(
                    display_product_links(checked_df),
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

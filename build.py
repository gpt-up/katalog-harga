import json, html, os, re, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

_config = {}
_config_path = ROOT / "config.json"
if _config_path.exists():
    _config = json.loads(_config_path.read_text(encoding="utf-8"))

SITE = os.environ.get("SITE_URL", _config.get("site_url", "https://harcoproducttechnologies.netlify.app")).rstrip("/")

with open(ROOT / "data/products.json", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

CATEGORIES = []
_categories_path = ROOT / "data/categories.json"
if _categories_path.exists():
    with open(_categories_path, encoding="utf-8") as f:
        CATEGORIES = json.load(f)

CATEGORY_BY_SLUG = {c["slug"]: c for c in CATEGORIES}

# Kategori yang ditonjolkan di homepage (section "Kategori Populer")
POPULAR_SLUGS = [
    "hpe-proliant-server",
    "dell-poweredge-server",
    "dell-optiplex-desktop",
    "dell-latitude-laptop",
    "dell-precision-workstation",
    "monitor-dell",
    "lenovo-legion-gaming-laptop",
    "lenovo-yoga-laptop",
]

# ---------- label dictionaries (brand/cat/line/model -> human labels) ----------
BRAND_LABEL = {"dell": "Dell Technologies", "hp": "HP Enterprise", "lenovo": "Lenovo"}

DELL_CAT = {
    "desktop-towers": "Desktop Towers", "aio": "All-In-Ones", "laptops": "Laptops",
    "workstations": "Workstations", "servers": "Servers", "storages": "Storages",
    "monitors": "Monitor Dell",
}
DELL_LINE = {
    "slim-desktop": "Dell SFF Desktop", "tower-desktop": "Dell Tower Desktop",
    "pro-slim-desktop": "Dell Pro Slim Desktop", "pro-micro-desktop": "Dell Pro Micro Desktop",
    "pro-slim-plus-desktop": "Dell Pro Slim Plus Desktop", "pro-micro-plus-desktop": "Dell Pro Micro Plus Desktop",
    "pro-max-tower-t2": "Dell Pro Max Tower T2 Desktop", "alienware-desktop": "Dell Alienware",
    "aio-24": "Dell 24 All-in-One Desktop", "aio-27": "Dell 27 All-in-One Desktop",
    "laptop": "Dell Laptop", "latitude": "Dell Latitude", "pro-laptop": "Dell Pro",
    "pro-2in1": "Dell Pro 2-in-1", "pro-plus-laptop": "Dell Pro Plus", "xps": "Dell XPS",
    "alienware-laptop": "Dell Alienware", "rugged": "Dell Rugged",
    "precision": "Dell Precision", "precision-mobile": "Dell Precision Mobile",
    "pro-precision": "Dell Pro Precision", "pro-max": "Dell Pro Max",
    "pro-max-tower": "Dell Pro Max Tower", "pro-max-micro": "Dell Pro Max Micro",
    "pro-max-slim": "Dell Pro Max Slim", "rackmount": "Rackmount", "tower-server": "Tower",
    "powervault": "Dell PowerVault", "powerstore": "Dell PowerStore",
}
DELL_MODEL = {
    "r260": "PowerEdge R260", "r360": "PowerEdge R360", "r660xs": "PowerEdge R660XS",
    "r660": "PowerEdge R660", "r760xs": "PowerEdge R760XS", "r760": "PowerEdge R760",
    "r860": "PowerEdge R860", "r960": "PowerEdge R960", "r760xd2": "PowerEdge R760XD2",
    "r470": "PowerEdge R470", "r570": "PowerEdge R570", "r670": "PowerEdge R670",
    "r770": "PowerEdge R770", "t160": "PowerEdge T160", "t360": "PowerEdge T360",
}
HP_CAT = {"servers": "Server"}
HP_LINE = {"rackmounts": "Rackmounts", "towers": "Towers", "part-options": "Part Options"}
HP_MODEL = {
    "microserver-gen10-plus-v2": "MicroServer Gen10 Plus v2", "microserver-gen11-sc": "MicroServer Gen11 SC",
    "dl20-gen10-plus": "ProLiant DL20 Gen10 Plus", "dl20-gen11": "ProLiant DL20 Gen11",
    "dl20-gen11-sc": "ProLiant DL20 Gen11 SC", "dl320-gen11-lff": "ProLiant DL320 Gen11 LFF",
    "dl320-gen11-lff-sc": "ProLiant DL320 Gen11 LFF SC", "dl320-gen11-sff-sc": "ProLiant DL320 Gen11 SFF SC",
    "dl325-gen11-sc": "ProLiant DL325 Gen11 SC", "dl360-gen11-8sff-sc": "ProLiant DL360 Gen11 8SFF SC",
    "dl380-gen10-8sff": "ProLiant DL380 Gen10 8SFF", "dl380-gen11-8sff": "ProLiant DL380 Gen11 8SFF",
    "dl380-gen11-8sff-sc": "ProLiant DL380 Gen11 8SFF SC", "dl385-gen11-8lff-sc": "ProLiant DL385 Gen11 8LFF SC",
    "dl385-gen11-8sff-sc": "ProLiant DL385 Gen11 8SFF SC",
    "ml30-gen11-4lff-sc": "ProLiant ML30 Gen11 4LFF SC", "ml110-gen11-4lff": "ProLiant ML110 Gen11 4LFF",
    "ml110-gen11-4lff-sc": "ProLiant ML110 Gen11 4LFF SC", "ml110-gen11-8sff": "ProLiant ML110 Gen11 8SFF",
    "ml110-gen11-8sff-sc": "ProLiant ML110 Gen11 8SFF SC", "ml350-gen11-8sff-sc": "ProLiant ML350 Gen11 8SFF SC",
}
LN_CAT = {"laptops": "Laptops", "aio": "All-In-Ones", "gaming": "Gaming Laptops"}
LN_LINE = {
    "yoga-slim": "Lenovo Yoga Slim 7", "yoga-2in1": "Lenovo Yoga 7 2-in-1",
    "yoga-9-2in1": "Lenovo Yoga 9 2-in-1", "yoga-book": "Lenovo Yoga Book 9",
    "yoga-pro": "Lenovo Yoga Pro 7", "ideapad-slim3": "Lenovo IdeaPad Slim 3",
    "ideapad-slim5": "Lenovo IdeaPad Slim 5", "ideapad-5-2in1": "Lenovo IdeaPad 5 2-in-1",
    "aio-24irh9": "Lenovo IdeaCentre AIO 24IRH9", "aio-v50a": "Lenovo AIO V50a-22IMB",
    "loq": "Lenovo LOQ", "legion-5": "Lenovo Legion 5", "legion-pro-5": "Lenovo Legion Pro 5",
    "legion-7": "Lenovo Legion 7",
}

def label(brand, kind, key):
    if not key:
        return None
    if brand == "dell":
        d = {"cat": DELL_CAT, "line": DELL_LINE, "model": DELL_MODEL}[kind]
    elif brand == "hp":
        d = {"cat": HP_CAT, "line": HP_LINE, "model": HP_MODEL}[kind]
    else:
        d = {"cat": LN_CAT, "line": LN_LINE, "model": {}}[kind]
    return d.get(key, key.replace("-", " ").title())

AVAIL_MAP = {
    "": "https://schema.org/InStock",
    "limited": "https://schema.org/LimitedAvailability",
    "last": "https://schema.org/LimitedAvailability",
    "indent": "https://schema.org/PreOrder",
    "otw": "https://schema.org/PreOrder",
    "check": "https://schema.org/LimitedAvailability",
}

TITLE_SUFFIX = " | HPT Jakarta"
MAX_TITLE_LEN = 70
MAX_DESC_LEN = 160

def truncate_at_word(text, max_len):
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0].rstrip(",.;-([")
    return cut + "…"

def build_product_title(model_name):
    budget = MAX_TITLE_LEN - len(TITLE_SUFFIX)
    return truncate_at_word(model_name, budget) + TITLE_SUFFIX

def build_product_description(model_name):
    prefix = "Harga "
    suffix = ". Garansi resmi, cek stok & penawaran di Harco Product Technologies Jakarta."
    suffix_after_ellipsis = " Garansi resmi, cek stok & penawaran di Harco Product Technologies Jakarta."
    budget = MAX_DESC_LEN - len(prefix) - len(suffix)
    if len(model_name) <= budget:
        return prefix + model_name + suffix
    return prefix + truncate_at_word(model_name, budget) + suffix_after_ellipsis

WA_NUMBER = "6285899992775"

def wa_link(model_name):
    text = f"Halo Harco Product Technologies, saya ingin tanya harga untuk {model_name}"
    return f"https://wa.me/{WA_NUMBER}?text={urllib.parse.quote(text)}"

def fmt_price(price):
    return "Rp. " + format(price, ",").replace(",", ".")

WA_ICON = '<svg viewBox="0 0 24 24" width="12" height="12" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l5.06-1.33C8.5 21.5 10.2 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm5.2 14.2c-.22.6-1.28 1.18-1.76 1.24-.45.06-.98.09-1.58-.1-.36-.11-.83-.27-1.43-.53-2.52-1.09-4.16-3.63-4.29-3.8-.13-.17-1.02-1.36-1.02-2.6 0-1.23.65-1.84.88-2.09.22-.25.49-.31.66-.31.17 0 .33 0 .48.01.15.01.36-.06.56.43.22.53.73 1.83.8 1.96.06.13.1.28.02.45-.09.17-.13.28-.26.43-.13.15-.27.34-.39.46-.13.13-.26.27-.11.53.15.26.66 1.09 1.42 1.77.98.87 1.8 1.14 2.06 1.27.26.13.41.11.56-.06.15-.17.65-.76.82-1.02.17-.26.34-.22.56-.13.22.09 1.42.67 1.66.79.24.11.4.17.46.27.06.11.06.61-.16 1.2z"/></svg>'

def category_url(slug):
    return f"{SITE}/{slug}/"

def filter_category_products(category, products):
    m = category["match"]
    def ok(p):
        if "brand" in m and p["brand"] != m["brand"]:
            return False
        if "cat" in m and p["cat"] != m["cat"]:
            return False
        if "line" in m:
            line = m["line"]
            if isinstance(line, list):
                if p["line"] not in line:
                    return False
            elif p["line"] != line:
                return False
        if "model" in m:
            mm = m["model"]
            if isinstance(mm, list):
                if p["model"] not in mm:
                    return False
            elif p["model"] != mm:
                return False
        if "name_contains" in m and m["name_contains"].lower() not in p["model_name"].lower():
            return False
        if "name_regex" in m and not re.search(m["name_regex"], p["model_name"]):
            return False
        return True
    return [p for p in products if ok(p)]

# ================= 1) RENDER PRODUCT ROWS (for index.html) =================

def render_row(p):
    attrs = f' data-cat="{p["cat"]}" data-line="{p["line"]}"' if p["cat"] else ""
    if p["brand"] != "dell":
        attrs = f' data-brand="{p["brand"]}"' + attrs
    if p["model"]:
        attrs += f' data-model="{p["model"]}"'

    specs_html = "\n".join(
        f'          <li{" class=\"hi\"" if s["hi"] else ""}>{html.escape(s["text"], quote=False)}</li>'
        for s in p["specs"]
    )

    if p["status_text"]:
        cls = f' {p["status_class"]}' if p["status_class"] else ""
        status_html = f'<span class="status-badge{cls}">{html.escape(p["status_text"], quote=False)}</span>'
    else:
        status_html = "&mdash;"

    if p["is_call"]:
        href = wa_link(p["model_name"])
        wa_icon = '<svg viewBox="0 0 24 24" width="12" height="12" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l5.06-1.33C8.5 21.5 10.2 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm5.2 14.2c-.22.6-1.28 1.18-1.76 1.24-.45.06-.98.09-1.58-.1-.36-.11-.83-.27-1.43-.53-2.52-1.09-4.16-3.63-4.29-3.8-.13-.17-1.02-1.36-1.02-2.6 0-1.23.65-1.84.88-2.09.22-.25.49-.31.66-.31.17 0 .33 0 .48.01.15.01.36-.06.56.43.22.53.73 1.83.8 1.96.06.13.1.28.02.45-.09.17-.13.28-.26.43-.13.15-.27.34-.39.46-.13.13-.26.27-.11.53.15.26.66 1.09 1.42 1.77.98.87 1.8 1.14 2.06 1.27.26.13.41.11.56-.06.15-.17.65-.76.82-1.02.17-.26.34-.22.56-.13.22.09 1.42.67 1.66.79.24.11.4.17.46.27.06.11.06.61-.16 1.2z"/></svg>'
        price_html = f'<a href="{href}" target="_blank" class="call-btn">{wa_icon}Tanya Harga</a>'
    else:
        price_html = fmt_price(p["price"])

    model_name_esc = html.escape(p["model_name"], quote=False)

    return f"""    <tr class="product-row"{attrs}>
      <td>
        {p["thumb_svg"]}
      </td>
      <td>
        <div class="model-line">{html.escape(p["model_line"], quote=False)}</div>
        <div class="model-name"><a href="produk/{p["slug"]}.html">{model_name_esc}</a></div>
      </td>
      <td>
        <ul class="specs">
{specs_html}
        </ul>
      </td>
      <td class="status-cell">{status_html}</td>
      <td class="price-cell">{price_html}</td>
    </tr>"""

rows_html = "\n\n".join(render_row(p) for p in PRODUCTS)

# ================= 2) RENDER ITEMLIST JSON-LD (1:1 with visible data) =================

itemlist = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": [],
}
for i, p in enumerate(PRODUCTS, start=1):
    canonical = f"{SITE}/produk/{p['slug']}.html"
    item = {
        "@type": "Product",
        "name": p["model_name"],
        "brand": {"@type": "Brand", "name": BRAND_LABEL.get(p["brand"], p["brand"].title())},
        "url": canonical,
    }
    if not p["is_call"] and p["price"] is not None:
        offer = {
            "@type": "Offer",
            "price": str(p["price"]),
            "priceCurrency": "IDR",
            "url": canonical,
        }
        if p["status_text"]:
            offer["availability"] = AVAIL_MAP.get(p["status_class"] or "", "https://schema.org/InStock")
        item["offers"] = offer
    itemlist["itemListElement"].append({
        "@type": "ListItem",
        "position": i,
        "item": item,
    })

itemlist_json = json.dumps(itemlist, ensure_ascii=False, indent=2)

# ================= 3) BUILD index.html FROM SHELL =================

# "Kategori Populer" section for homepage (only non-empty popular categories)
_pop_links = []
for slug in POPULAR_SLUGS:
    cat = CATEGORY_BY_SLUG.get(slug)
    if cat and filter_category_products(cat, PRODUCTS):
        _pop_links.append(f'    <a href="{slug}/">{html.escape(cat["h1"], quote=False)}</a>')

if _pop_links:
    popular_html = (
        '<section class="popcat">\n'
        '  <h2>Kategori Populer</h2>\n'
        '  <div class="popcat-links">\n'
        + "\n".join(_pop_links) + "\n"
        '  </div>\n'
        '</section>'
    )
else:
    popular_html = ""

with open(ROOT / "templates/index_shell.html", encoding="utf-8") as f:
    shell = f.read()

final_index = (
    shell.replace("{{ITEMLIST_JSONLD}}", itemlist_json)
    .replace("{{PRODUCT_ROWS}}", rows_html)
    .replace("{{POPULAR_CATEGORIES}}", popular_html)
    .replace("{{SITE}}", SITE)
)

with open(ROOT / "index.html", "w", encoding="utf-8") as f:
    f.write(final_index)

print("index.html written:", len(final_index), "bytes")

# ================= 4) BUILD 564 PRODUCT PAGES =================

PRODUCT_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="product">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">

<link rel="canonical" href="{canonical}">

<script type="application/ld+json">
{jsonld}
</script>

<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/product.css">
</head>
<body>

<div class="topbar">
  <div class="brand">
    <a href="../index.html"><img src="../assets/img/logo/Logo-HPT.png" alt="Harco Product Technologies" class="brand-logo"></a>
  </div>
  <div class="address">
    <b>Alamat:</b><br>
    <b>Harco Product Technologies</b><br>
    Harco Mangga Dua Plaza Lt. 1 Blok A1 No. 15<br>
    Jl. Mangga Dua Raya, Kel. Mangga Dua Selatan<br>
    Jakarta Pusat - 10730 | Whatsapp: 0858.9999.2775<br>
    <a href="https://wa.me/6285899992775?text=Halo%20Harco%20Product%20Technologies%2C%20saya%20ingin%20tanya%20produk" target="_blank" class="wa-btn">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l5.06-1.33C8.5 21.5 10.2 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm5.2 14.2c-.22.6-1.28 1.18-1.76 1.24-.45.06-.98.09-1.58-.1-.36-.11-.83-.27-1.43-.53-2.52-1.09-4.16-3.63-4.29-3.8-.13-.17-1.02-1.36-1.02-2.6 0-1.23.65-1.84.88-2.09.22-.25.49-.31.66-.31.17 0 .33 0 .48.01.15.01.36-.06.56.43.22.53.73 1.83.8 1.96.06.13.1.28.02.45-.09.17-.13.28-.26.43-.13.15-.27.34-.39.46-.13.13-.26.27-.11.53.15.26.66 1.09 1.42 1.77.98.87 1.8 1.14 2.06 1.27.26.13.41.11.56-.06.15-.17.65-.76.82-1.02.17-.26.34-.22.56-.13.22.09 1.42.67 1.66.79.24.11.4.17.46.27.06.11.06.61-.16 1.2z"/></svg>
      Chat WhatsApp
    </a>
  </div>
</div>

<div class="wrap">
<p class="crumb">{breadcrumb}</p>

<div class="product-detail">
  <div class="pd-thumb">{thumb}</div>
  <div class="pd-info">
    <div class="pd-line">{model_line}</div>
    <h1 class="pd-name">{model_name}</h1>
    <ul class="specs">
{specs}
    </ul>
    <div class="pd-bottom">
      {status_html}
      <div class="pd-price">{price_html}</div>
    </div>
  </div>
</div>

<p class="back-link"><a href="../index.html">&larr; Kembali ke Katalog Lengkap</a></p>
</div>

<footer id="siteFooter">
  <p>&copy; 2026 Harco Product Technologies &mdash; {brand_label} Authorized Reseller.</p>
  <p>Harco Mangga Dua Plaza Lt. 1 Blok A1 No. 15, Jl. Mangga Dua Raya, Kel. Mangga Dua Selatan, Jakarta Pusat - 10730. Whatsapp: <a href="https://wa.me/6285899992775" target="_blank">0858.9999.2775</a>.</p>
  <p>Harga sewaktu-waktu dapat berubah.</p>
</footer>

</body>
</html>
"""

os.makedirs(ROOT / "produk", exist_ok=True)
sitemap_urls = []

for p in PRODUCTS:
    brand_label = BRAND_LABEL.get(p["brand"], p["brand"].title())
    cat_label = label(p["brand"], "cat", p["cat"])
    line_label = label(p["brand"], "line", p["line"])
    model_label = label(p["brand"], "model", p["model"]) if p["model"] else None

    crumb_parts = ['<a href="../index.html">Home</a>', brand_label]
    if cat_label: crumb_parts.append(cat_label)
    if line_label: crumb_parts.append(line_label)
    if model_label: crumb_parts.append(model_label)
    breadcrumb = " &rsaquo; ".join(crumb_parts) + " &rsaquo; " + html.escape(p["model_name"], quote=False)

    specs_items = [
        f'      <li{" class=\"hi\"" if s["hi"] else ""}>{html.escape(s["text"], quote=False)}</li>'
        for s in p["specs"]
    ]

    if p["is_call"]:
        href = wa_link(p["model_name"])
        wa_icon = '<svg viewBox="0 0 24 24" width="12" height="12" fill="#fff"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l5.06-1.33C8.5 21.5 10.2 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm5.2 14.2c-.22.6-1.28 1.18-1.76 1.24-.45.06-.98.09-1.58-.1-.36-.11-.83-.27-1.43-.53-2.52-1.09-4.16-3.63-4.29-3.8-.13-.17-1.02-1.36-1.02-2.6 0-1.23.65-1.84.88-2.09.22-.25.49-.31.66-.31.17 0 .33 0 .48.01.15.01.36-.06.56.43.22.53.73 1.83.8 1.96.06.13.1.28.02.45-.09.17-.13.28-.26.43-.13.15-.27.34-.39.46-.13.13-.26.27-.11.53.15.26.66 1.09 1.42 1.77.98.87 1.8 1.14 2.06 1.27.26.13.41.11.56-.06.15-.17.65-.76.82-1.02.17-.26.34-.22.56-.13.22.09 1.42.67 1.66.79.24.11.4.17.46.27.06.11.06.61-.16 1.2z"/></svg>'
        price_html = f'<a href="{href}" target="_blank" class="call-btn">{wa_icon}Tanya Harga</a>'
        offers = None
    else:
        price_html = fmt_price(p["price"])
        offers = {
            "@type": "Offer",
            "price": str(p["price"]),
            "priceCurrency": "IDR",
            "url": f"{SITE}/produk/{p['slug']}.html",
        }
        if p["status_text"]:
            offers["availability"] = AVAIL_MAP.get(p["status_class"] or "", "https://schema.org/InStock")

    if p["status_text"]:
        cls = f' {p["status_class"]}' if p["status_class"] else ""
        status_html = f'<span class="status-badge{cls}">{html.escape(p["status_text"], quote=False)}</span>'
    else:
        status_html = ""

    description = build_product_description(p["model_name"])
    description_attr = html.escape(description, quote=True)

    canonical = f"{SITE}/produk/{p['slug']}.html"

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["model_name"],
        "description": description,
        "brand": {"@type": "Brand", "name": brand_label},
        "url": canonical,
    }
    if offers:
        jsonld["offers"] = offers

    html_out = PRODUCT_TEMPLATE.format(
        title=html.escape(build_product_title(p["model_name"]), quote=False),
        description=description_attr,
        og_title=html.escape(build_product_title(p["model_name"]), quote=True),
        canonical=canonical,
        jsonld=json.dumps(jsonld, ensure_ascii=False, indent=2),
        breadcrumb=breadcrumb,
        thumb=p["thumb_svg"],
        model_line=html.escape(p["model_line"], quote=False),
        model_name=html.escape(p["model_name"], quote=False),
        specs="\n".join(specs_items),
        status_html=status_html,
        price_html=price_html,
        brand_label=brand_label,
    )

    with open(ROOT / "produk" / f"{p['slug']}.html", "w", encoding="utf-8") as f:
        f.write(html_out)

    sitemap_urls.append(canonical)

print("Product pages written:", len(PRODUCTS))

# ================= 5) BUILD CATEGORY LANDING PAGES =================

CATEGORY_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="website">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">

<link rel="canonical" href="{canonical}">

<script type="application/ld+json">
{jsonld}
</script>

<link rel="stylesheet" href="../assets/css/style.css">
<link rel="stylesheet" href="../assets/css/category.css">
</head>
<body>

<div class="topbar">
  <div class="brand">
    <a href="../index.html"><img src="../assets/img/logo/Logo-HPT.png" alt="Harco Product Technologies" class="brand-logo"></a>
  </div>
  <div class="address">
    <b>Alamat:</b><br>
    <b>Harco Product Technologies</b><br>
    Harco Mangga Dua Plaza Lt. 1 Blok A1 No. 15<br>
    Jl. Mangga Dua Raya, Kel. Mangga Dua Selatan<br>
    Jakarta Pusat - 10730 | Whatsapp: 0858.9999.2775<br>
    <a href="https://wa.me/6285899992775?text=Halo%20Harco%20Product%20Technologies%2C%20saya%20ingin%20tanya%20produk" target="_blank" class="wa-btn">
      {wa_icon}
      Chat WhatsApp
    </a>
  </div>
</div>

<div class="wrap">
<p class="crumb">{breadcrumb}</p>

<div class="cat-head">
  <h1>{h1}</h1>
  <p class="cat-count">{count} produk tersedia</p>
  <div class="cat-intro">
{intro}
  </div>
  <a href="{wa_cta}" target="_blank" class="cat-cta">{wa_icon} Konsultasi &amp; Tanya Harga via WhatsApp</a>
</div>

<div class="cat-grid">
{cards}
</div>

<div class="cat-related">
  <h2>Kategori Terkait</h2>
  <div class="cat-related-links">
{related}
  </div>
</div>

<p class="back-link"><a href="../index.html">&larr; Lihat Katalog Lengkap</a></p>
</div>

<footer id="siteFooter">
  <p>&copy; 2026 Harco Product Technologies &mdash; Dell, HP Enterprise &amp; Lenovo Authorized Reseller.</p>
  <p>Harco Mangga Dua Plaza Lt. 1 Blok A1 No. 15, Jl. Mangga Dua Raya, Kel. Mangga Dua Selatan, Jakarta Pusat - 10730. Whatsapp: <a href="https://wa.me/6285899992775" target="_blank">0858.9999.2775</a>.</p>
  <p>Harga sewaktu-waktu dapat berubah.</p>
</footer>

</body>
</html>
"""

def render_category_card(p):
    name_esc = html.escape(p["model_name"], quote=False)
    line_esc = html.escape(p["model_line"], quote=False)

    specs_top = p["specs"][:3]
    specs_html = "\n".join(
        f'      <li{" class=\"hi\"" if s["hi"] else ""}>{html.escape(s["text"], quote=False)}</li>'
        for s in specs_top
    )

    if p["status_text"]:
        cls = f' {p["status_class"]}' if p["status_class"] else ""
        status_html = f'<span class="status-badge{cls}">{html.escape(p["status_text"], quote=False)}</span>'
    else:
        status_html = ""

    if p["is_call"]:
        price_html = f'<a href="{wa_link(p["model_name"])}" target="_blank" class="call-btn">{WA_ICON}Tanya Harga</a>'
    else:
        price_html = f'<span class="cat-card-price">{fmt_price(p["price"])}</span>'

    return f"""  <div class="cat-card">
    <div class="cat-card-line">{line_esc}</div>
    <div class="cat-card-name"><a href="../produk/{p["slug"]}.html">{name_esc}</a></div>
    {status_html}
    <ul class="specs">
{specs_html}
    </ul>
    <div class="cat-card-foot">
      {price_html}
      <div class="cat-card-actions">
        <a class="cat-detail-link" href="../produk/{p["slug"]}.html">Lihat Detail &rsaquo;</a>
      </div>
    </div>
  </div>"""

def render_category_jsonld(category, products):
    canonical = category_url(category["slug"])
    collection = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": category["h1"],
        "description": category["description"],
        "url": canonical,
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Beranda", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": category["h1"], "item": canonical},
        ],
    }
    itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [],
    }
    for i, p in enumerate(products, start=1):
        purl = f"{SITE}/produk/{p['slug']}.html"
        item = {
            "@type": "Product",
            "name": p["model_name"],
            "brand": {"@type": "Brand", "name": BRAND_LABEL.get(p["brand"], p["brand"].title())},
            "url": purl,
        }
        if not p["is_call"] and p["price"] is not None:
            offer = {"@type": "Offer", "price": str(p["price"]), "priceCurrency": "IDR", "url": purl}
            if p["status_text"]:
                offer["availability"] = AVAIL_MAP.get(p["status_class"] or "", "https://schema.org/InStock")
            item["offers"] = offer
        itemlist["itemListElement"].append({"@type": "ListItem", "position": i, "item": item})
    return json.dumps([collection, breadcrumb, itemlist], ensure_ascii=False, indent=2)

def render_category_page(category, products):
    canonical = category_url(category["slug"])
    intro_html = "\n".join(
        f"    <p>{html.escape(par, quote=False)}</p>" for par in category["intro"]
    )
    cards_html = "\n".join(render_category_card(p) for p in products)

    breadcrumb = (
        '<a href="../index.html">Beranda</a> &rsaquo; Kategori &rsaquo; '
        + html.escape(category["h1"], quote=False)
    )

    related_links = []
    for rslug in category.get("related", []):
        rcat = CATEGORY_BY_SLUG.get(rslug)
        if rcat:
            related_links.append(
                f'    <a href="../{rslug}/">{html.escape(rcat["h1"], quote=False)}</a>'
            )
    related_html = "\n".join(related_links)

    wa_cta = f"https://wa.me/{WA_NUMBER}?text=" + urllib.parse.quote(
        f"Halo Harco Product Technologies, saya ingin tanya {category['h1']}"
    )

    return CATEGORY_TEMPLATE.format(
        title=html.escape(category["title"], quote=False),
        description=html.escape(category["description"], quote=True),
        og_title=html.escape(category.get("og_title", category["title"]), quote=True),
        canonical=canonical,
        jsonld=render_category_jsonld(category, products),
        breadcrumb=breadcrumb,
        h1=html.escape(category["h1"], quote=False),
        count=len(products),
        intro=intro_html,
        cards=cards_html,
        related=related_html,
        wa_cta=wa_cta,
        wa_icon=WA_ICON,
    )

category_urls = []
category_report = []
for category in CATEGORIES:
    matched = filter_category_products(category, PRODUCTS)
    if not matched:
        category_report.append((category["slug"], 0, "SKIPPED (kosong)"))
        continue
    out_dir = ROOT / category["slug"]
    os.makedirs(out_dir, exist_ok=True)
    with open(out_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(render_category_page(category, matched))
    category_urls.append(category_url(category["slug"]))
    category_report.append((category["slug"], len(matched), "OK"))

print("Category pages written:", len(category_urls))
for slug, n, status in category_report:
    print(f"  {slug:38} {n:>4} produk  {status}")

# ================= 6) BUILD sitemap.xml =================

lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
lines.append('  <url>')
lines.append(f'    <loc>{SITE}/</loc>')
lines.append('    <changefreq>daily</changefreq>')
lines.append('    <priority>1.0</priority>')
lines.append('  </url>')
for u in category_urls:
    lines.append('  <url>')
    lines.append(f'    <loc>{u}</loc>')
    lines.append('    <changefreq>weekly</changefreq>')
    lines.append('    <priority>0.85</priority>')
    lines.append('  </url>')
for u in sitemap_urls:
    lines.append('  <url>')
    lines.append(f'    <loc>{u}</loc>')
    lines.append('    <changefreq>weekly</changefreq>')
    lines.append('    <priority>0.8</priority>')
    lines.append('  </url>')
lines.append('</urlset>')
lines.append('')
with open(ROOT / "sitemap.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("sitemap.xml written, total URLs:", 1 + len(category_urls) + len(sitemap_urls))

# ================= 7) BUILD robots.txt =================

robots_txt = f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
with open(ROOT / "robots.txt", "w", encoding="utf-8") as f:
    f.write(robots_txt)

print("robots.txt written")

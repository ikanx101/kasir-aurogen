import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

MONTH_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
]

BOLD_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf",
]

LOGO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "static", "logo_utama.jpeg"
)


def _get_font(paths: list, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def format_rupiah(amount: int) -> str:
    return f"{amount:,}".replace(",", ".")


def generate_struk(
    event_name: str,
    transaction_number: str,
    items: list,
    total: int,
    created_at: datetime,
    output_path: str,
    customer_name: str = None,
    customer_phone: str = None,
    payment_method: str = "tunai",
) -> str:
    SCALE = 2
    WIDTH = 600
    BG_COLOR = (255, 255, 255)
    TEXT_COLOR = (26, 26, 26)
    BORDER_COLOR = (60, 60, 60)

    PAD_X = 28 * SCALE
    PAD_Y = 20 * SCALE
    LINE_H = 20 * SCALE
    SECTION_GAP = 10 * SCALE

    SIZE_STORE = 22 * SCALE
    SIZE_EVENT = 15 * SCALE
    SIZE_NORMAL = 14 * SCALE
    SIZE_TOTAL = 16 * SCALE

    font_normal = _get_font(FONT_PATHS, SIZE_NORMAL)
    font_bold = _get_font(BOLD_FONT_PATHS, SIZE_STORE)
    font_event = _get_font(FONT_PATHS, SIZE_EVENT)
    font_total = _get_font(BOLD_FONT_PATHS, SIZE_TOTAL)
    font_item = _get_font(FONT_PATHS, SIZE_NORMAL)

    CONTENT_W = WIDTH * SCALE - PAD_X * 2

    # Load logo (optional)
    logo_pil = None
    logo_height_px = 0
    if os.path.exists(LOGO_PATH):
        try:
            raw = Image.open(LOGO_PATH).convert("RGB")
            max_logo_w = 180 * SCALE
            max_logo_h = 80 * SCALE
            ratio = min(max_logo_w / raw.width, max_logo_h / raw.height)
            new_w = int(raw.width * ratio)
            new_h = int(raw.height * ratio)
            logo_pil = raw.resize((new_w, new_h), Image.LANCZOS)
            logo_height_px = new_h
        except Exception:
            pass

    # Measure text bbox helper — returns (left_offset, width)
    def text_bbox_info(text, font):
        try:
            dummy = Image.new("RGB", (1, 1))
            d = ImageDraw.Draw(dummy)
            bbox = d.textbbox((0, 0), text, font=font)
            return bbox[0], bbox[2] - bbox[0]
        except Exception:
            return 0, len(text) * SIZE_NORMAL // 2

    # Format datetime
    wib_offset = 7 * 3600
    local_dt = datetime.utcfromtimestamp(created_at.timestamp() + wib_offset)
    date_str = f"{local_dt.day} {MONTH_ID[local_dt.month]} {local_dt.year}"
    time_str = local_dt.strftime("%H:%M") + " WIB"
    datetime_str = f"{date_str}  {time_str}"

    sep_line = "─" * 42

    item_lines = []
    for it in items:
        name = it["name"]
        qty = it["qty"]
        price = it["price"]
        subtotal = it["subtotal"]
        price_str = f"{qty} x {format_rupiah(price)}"
        sub_str = format_rupiah(subtotal)
        item_lines.append((name, price_str, sub_str))

    # Estimate height (image is cropped to actual content at the end)
    n_header = 6 + 1  # sep + logo + store + event + datetime + tx# + sep
    n_customer = 1 + (1 if customer_name else 0) + (1 if customer_phone else 0)  # payment + optional fields + sep
    n_items = len(item_lines) + 2
    n_footer = 5
    total_lines = n_header + n_customer + n_items + n_footer
    HEIGHT = (
        PAD_Y * 2
        + total_lines * (LINE_H + 4 * SCALE)
        + SECTION_GAP * 4
        + logo_height_px
        + SECTION_GAP * 2
    )

    img = Image.new("RGB", (WIDTH * SCALE, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = PAD_Y

    def draw_centered(text, font, color=TEXT_COLOR):
        nonlocal y
        left_off, w = text_bbox_info(text, font)
        x = (WIDTH * SCALE - w) // 2 - left_off
        draw.text((x, y), text, font=font, fill=color)
        y += LINE_H + 4 * SCALE

    def draw_left(text, font, color=TEXT_COLOR):
        nonlocal y
        draw.text((PAD_X, y), text, font=font, fill=color)
        y += LINE_H + 4 * SCALE

    def draw_sep(char="─", bold=False):
        nonlocal y
        line = char * 42
        f = font_total if bold else font_item
        left_off, w = text_bbox_info(line, f)
        x = (WIDTH * SCALE - w) // 2 - left_off
        draw.text((x, y), line, font=f, fill=BORDER_COLOR)
        y += LINE_H + 4 * SCALE

    def draw_item_row(name, price_str, sub_str):
        nonlocal y
        max_name = 18
        if len(name) > max_name:
            name = name[:max_name - 1] + "…"
        row = f"{name:<18} {price_str:>12}  {sub_str:>8}"
        draw.text((PAD_X, y), row, font=font_item, fill=TEXT_COLOR)
        y += LINE_H + 4 * SCALE

    def draw_total_row(label, value):
        nonlocal y
        row = f"{label:<18} {'':>12}  {value:>8}"
        draw.text((PAD_X, y), row, font=font_total, fill=TEXT_COLOR)
        y += LINE_H + 4 * SCALE

    # Header
    draw_sep("═", bold=True)

    # Logo (centered, if available)
    if logo_pil is not None:
        x_logo = (WIDTH * SCALE - logo_pil.width) // 2
        img.paste(logo_pil, (x_logo, y))
        y += logo_height_px + SECTION_GAP

    draw_centered("Dapoerasatoe", font_bold)
    draw_centered(event_name, font_event)
    draw_centered(datetime_str, font_item)
    draw_centered(f"No: {transaction_number}", font_item)
    draw_sep("─")

    # Customer & payment info
    if customer_name:
        draw_left(f"Pelanggan : {customer_name[:26]}", font_item)
    if customer_phone:
        draw_left(f"HP/WA     : {customer_phone[:26]}", font_item)
    pay_label = "TUNAI" if payment_method == "tunai" else "QRIS"
    draw_left(f"Pembayaran: {pay_label}", font_item)
    draw_sep("─")

    # Items
    for name, price_str, sub_str in item_lines:
        draw_item_row(name, price_str, sub_str)
    draw_sep("─")

    # Total
    draw_total_row("TOTAL", f"Rp {format_rupiah(total)}")
    draw_sep("─")

    # Footer
    draw_centered("Terima kasih sudah berkunjung!", font_item)
    draw_centered("Semoga berkah :)", font_item)
    draw_sep("═", bold=True)

    # Crop to actual content
    img = img.crop((0, 0, WIDTH * SCALE, y + PAD_Y))
    img.save(output_path, "PNG", dpi=(300, 300))
    return output_path

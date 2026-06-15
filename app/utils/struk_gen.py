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
    WIDTH = 380  # Narrow like thermal/minimarket receipt
    BG_COLOR = (255, 255, 255)
    TEXT_COLOR = (26, 26, 26)
    BORDER_COLOR = (60, 60, 60)

    PAD_X = 20 * SCALE
    PAD_Y = 16 * SCALE
    LINE_H = 18 * SCALE
    SECTION_GAP = 8 * SCALE

    SIZE_STORE = 20 * SCALE
    SIZE_EVENT = 13 * SCALE
    SIZE_NORMAL = 12 * SCALE
    SIZE_TOTAL = 13 * SCALE

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
            max_logo_w = 140 * SCALE
            max_logo_h = 55 * SCALE
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
        f = font_total if bold else font_item
        _, char_w = text_bbox_info(char, f)
        n_chars = max(1, (WIDTH * SCALE - PAD_X * 2) // char_w) if char_w > 0 else 36
        line = char * n_chars
        draw.text((PAD_X, y), line, font=f, fill=BORDER_COLOR)
        y += LINE_H + 4 * SCALE

    def draw_item_row(name, price_str, sub_str):
        nonlocal y
        # Draw name on the left, subtotal pixel-right-aligned, price in between
        max_name = 16
        if len(name) > max_name:
            name = name[:max_name - 1] + "…"
        draw.text((PAD_X, y), name, font=font_item, fill=TEXT_COLOR)
        # Subtotal right-aligned
        left_off_s, w_s = text_bbox_info(sub_str, font_item)
        x_sub = WIDTH * SCALE - PAD_X - w_s - left_off_s
        draw.text((x_sub, y), sub_str, font=font_item, fill=TEXT_COLOR)
        # Price string just to the left of subtotal (clamped to stay right of name area)
        left_off_p, w_p = text_bbox_info(price_str, font_item)
        x_price = max(PAD_X, x_sub - w_p - left_off_p - (6 * SCALE))
        draw.text((x_price, y), price_str, font=font_item, fill=(100, 100, 100))
        y += LINE_H + 4 * SCALE

    def draw_total_row(label, value):
        nonlocal y
        draw.text((PAD_X, y), label, font=font_total, fill=TEXT_COLOR)
        left_off, w = text_bbox_info(value, font_total)
        x_right = WIDTH * SCALE - PAD_X - w - left_off
        draw.text((x_right, y), value, font=font_total, fill=TEXT_COLOR)
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

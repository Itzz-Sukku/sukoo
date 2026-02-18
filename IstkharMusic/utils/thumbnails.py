import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ====== FULL HD SETTINGS ======
WIDTH, HEIGHT = 1920, 1080

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

PANEL_W, PANEL_H = 1100, 750
PANEL_X = (WIDTH - PANEL_W) // 2
PANEL_Y = (HEIGHT - PANEL_H) // 2
TRANSPARENCY = 180
INNER_OFFSET = 60

THUMB_W, THUMB_H = 820, 420
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + INNER_OFFSET

TITLE_Y = THUMB_Y + THUMB_H + 30
META_Y = TITLE_Y + 70

BAR_Y = META_Y + 80
BAR_X = PANEL_X + 150
BAR_RED_LEN = 400
BAR_TOTAL_LEN = 700

ICONS_W, ICONS_H = 600, 80
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 80

MAX_TITLE_WIDTH = 900


def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_FHD.png")
    if os.path.exists(cache_path):
        return cache_path

    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    try:
        results_data = await results.next()
        data = results_data["result"][0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception:
        title, thumbnail, duration, views = "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views"

    is_live = not duration or str(duration).lower() in {"", "live", "live now"}
    duration_text = "Live" if is_live else duration or "Unknown"

    thumb_path = os.path.join(CACHE_DIR, f"thumb{videoid}.png")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except:
        return YOUTUBE_IMG_URL

    base = Image.open(thumb_path).resize((WIDTH, HEIGHT)).convert("RGBA")
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(25))).enhance(0.55)

    # Frosted panel
    panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
    overlay = Image.new("RGBA", (PANEL_W, PANEL_H), (255, 255, 255, TRANSPARENCY))
    frosted = Image.alpha_composite(panel_area, overlay)

    mask = Image.new("L", (PANEL_W, PANEL_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, PANEL_W, PANEL_H), 60, fill=255)
    bg.paste(frosted, (PANEL_X, PANEL_Y), mask)

    draw = ImageDraw.Draw(bg)

    try:
        title_font = ImageFont.truetype("IstkharMusic/assets/font2.ttf", 55)
        regular_font = ImageFont.truetype("IstkharMusic/assets/font.ttf", 35)
    except:
        title_font = regular_font = ImageFont.load_default()

    # Thumbnail
    thumb = base.resize((THUMB_W, THUMB_H))
    tmask = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tmask).rounded_rectangle((0, 0, THUMB_W, THUMB_H), 40, fill=255)
    bg.paste(thumb, (THUMB_X, THUMB_Y), tmask)

    # Title
    title = trim_to_width(title, title_font, MAX_TITLE_WIDTH)
    title_w = title_font.getlength(title)
    draw.text(
        ((WIDTH - title_w) / 2, TITLE_Y),
        title,
        fill="black",
        font=title_font,
    )

    # Meta
    meta_text = f"YouTube | {views}"
    meta_w = regular_font.getlength(meta_text)
    draw.text(
        ((WIDTH - meta_w) / 2, META_Y),
        meta_text,
        fill="black",
        font=regular_font,
    )

    # Progress bar
    draw.line([(BAR_X, BAR_Y), (BAR_X + BAR_RED_LEN, BAR_Y)], fill="red", width=10)
    draw.line([(BAR_X + BAR_RED_LEN, BAR_Y), (BAR_X + BAR_TOTAL_LEN, BAR_Y)], fill="gray", width=8)

    draw.ellipse(
        [(BAR_X + BAR_RED_LEN - 12, BAR_Y - 12),
         (BAR_X + BAR_RED_LEN + 12, BAR_Y + 12)],
        fill="red"
    )

    draw.text((BAR_X, BAR_Y + 20), "00:00", fill="black", font=regular_font)

    end_text = "Live" if is_live else duration_text
    draw.text(
        (BAR_X + BAR_TOTAL_LEN - 120, BAR_Y + 20),
        end_text,
        fill="red" if is_live else "black",
        font=regular_font
    )

    # Icons
    icons_path = "IstkharMusic/assets/play_icons.png"
    if os.path.isfile(icons_path):
        ic = Image.open(icons_path).resize((ICONS_W, ICONS_H)).convert("RGBA")
        bg.paste(ic, (ICONS_X, ICONS_Y), ic)

    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(cache_path, quality=95)
    return cache_path

from PIL import Image, ImageDraw, ImageFont


def generate_thumbnail(text, output_path):

    width = 800
    height = 400

    img = Image.new("RGB", (width, height), color=(30, 30, 30))

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    # ---- FIX HERE ----
    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    img.save(output_path)
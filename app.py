from flask import Flask, render_template, request, jsonify, send_from_directory
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import (
    SquareModuleDrawer,
    RoundedModuleDrawer,
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
)
import io
import base64
import os

app = Flask(__name__)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = "".join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.png",
        mimetype="image/png"
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    url = data.get("url", "").strip()
    dark_color = data.get("dark_color", "#3d1a2e").strip()
    light_color = data.get("light_color", "#ffffff").strip()
    shape = data.get("shape", "square").strip()
    try:
        size = int(data.get("size", 10))
    except (ValueError, TypeError):
        size = 10

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Determine the module drawer to use
        if shape == "rounded":
            drawer = RoundedModuleDrawer()
        elif shape == "circle":
            drawer = CircleModuleDrawer()
        elif shape == "gapped":
            drawer = GappedSquareModuleDrawer()
        else:
            drawer = SquareModuleDrawer()

        # Parse colors
        front_rgb = hex_to_rgb(dark_color)
        back_rgb = hex_to_rgb(light_color)

        # Generate QR code
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=drawer,
            color_mask=SolidFillColorMask(front_color=front_rgb, back_color=back_rgb)
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return jsonify({"image": f"data:image/png;base64,{img_base64}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

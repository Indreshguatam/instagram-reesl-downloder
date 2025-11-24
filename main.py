from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, Response, send_file
)
import yt_dlp
import requests
from urllib.parse import urlparse
import os

# -------------------------
# Configuration
# -------------------------
app = Flask(__name__)
app.secret_key = "change_this_secret"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# -------------------------
# Helpers
# -------------------------
def is_instagram_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.netloc and "instagram.com" in u.netloc.lower()
    except:
        return False

def clean_url(url: str) -> str:
    if not url:
        return url
    if "?" in url:
        url = url.split("?", 1)[0]
    return url.strip()

def pick_best_format(info: dict) -> str:
    if info.get("url") and info.get("acodec", "") != "none":
        return info.get("url")

    formats = info.get("formats") or []
    http_formats = [f for f in formats if f.get("protocol", "").startswith("http")]
    if not http_formats:
        return None

    http_formats.sort(key=lambda f: ((f.get("height") or 0), (f.get("tbr") or 0)), reverse=True)

    for f in http_formats:
        if f.get("ext") in ("mp4", "m4a", "mkv", "webm"):
            return f.get("url")

    return http_formats[0].get("url")

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_url = request.form.get("video_url", "").strip()

        if not raw_url:
            flash("Please paste an Instagram URL.", "error")
            return redirect(url_for("index"))

        url = clean_url(raw_url)

        if not is_instagram_url(url):
            flash("Invalid Instagram URL.", "error")
            return redirect(url_for("index"))

        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "http_headers": DEFAULT_HEADERS,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if info.get("entries"):
                info = info["entries"][0]

            media_url = pick_best_format(info)

            title = info.get("title") or "instagram_video"
            ext = info.get("ext") or "mp4"

            if not media_url:
                flash("Unable to get video. Post may be private.", "error")
                return redirect(url_for("index"))

            return render_template("index.html",
                                   preview=True,
                                   media_url=media_url,
                                   original_url=url,
                                   title=title,
                                   ext=ext)

        except Exception as e:
            print("extract error:", e)
            flash("Error fetching video. Post may be private.", "error")
            return redirect(url_for("index"))

    return render_template("index.html", preview=False)


# ---------------------------------------------
# DOWNLOAD WITH AUDIO (MERGED)
# ---------------------------------------------
@app.route("/download_merged", methods=["POST"])
def download_merged():
    url = request.form.get("original_url")

    if not url:
        flash("URL missing.", "error")
        return redirect(url_for("index"))

    output_file = "downloaded_instagram_video.mp4"

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_file,
        "quiet": True,
        "http_headers": DEFAULT_HEADERS,
    }

    try:
        if os.path.exists(output_file):
            os.remove(output_file)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(
            output_file,
            as_attachment=True,
            download_name="Instagram_Reel.mp4"
        )

    except Exception as e:
        print("merged download error:", e)
        flash("Could not download video with audio.", "error")
        return redirect(url_for("index"))


# -------------------------
# Legal Pages (Optional)
# -------------------------
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/dmca")
def dmca():
    return render_template("dmca.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)

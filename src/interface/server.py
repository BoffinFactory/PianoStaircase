from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="frontend") 

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    # This allows style.css and script.js to load too
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
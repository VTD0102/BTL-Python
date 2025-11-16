from flask import Flask, request, jsonify
import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "stats.db")

app = Flask(__name__)

# ==============================
# 2 Hàm tiện ích
# ==============================
def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ==============================
# 3 API: Tra cứu theo tên cầu thủ
# ==============================
@app.route("/player", methods=["GET"])
def get_player_by_name():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "Thiếu tham số ?name=<tên cầu thủ>"}), 400
    query = "SELECT * FROM PLAYER_STATS WHERE Player LIKE ? COLLATE NOCASE"
    results = query_db(query, (f"%{name}%",))
    if not results:
        return jsonify([]), 200
    return jsonify(results)


# ==============================
# 4 API: Tra cứu theo câu lạc bộ
# ==============================
@app.route("/club", methods=["GET"])
def get_players_by_club():
    club = request.args.get("club", "").strip()
    if not club:
        return jsonify({"error": "Thiếu tham số ?club=<tên câu lạc bộ>"}), 400
    query = "SELECT * FROM PLAYER_STATS WHERE Squad LIKE ? COLLATE NOCASE"
    results = query_db(query, (f"%{club}%",))

    if not results:
        return jsonify([]), 200

    return jsonify(results)


# ==============================
# 5 API mặc định
# ==============================
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "API tra cứu cầu thủ FBref + FootballTransfers",
        "endpoints": {
            "/player?name=<tên>": "Tra cứu theo tên cầu thủ",
            "/club?club=<clb>": "Tra cứu theo tên câu lạc bộ"
        }
    })


# ==============================
# 6 Main
# ==============================
if __name__ == "__main__":
    print(f"API đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True)

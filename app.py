import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
import io
from collections import Counter

# 🔹 Bendri nustatymai
st.set_page_config(page_title="Kortų Optimizatorius", layout="centered")

# ======================
# 📱 MOBILI VERSIJA
# ======================
st.markdown("""
<style>
    .stTextInput > div > div > input {
        font-size: 20px !important;
        text-align: center;
    }
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 22px;
        background-color: #2b8a3e;
        color: white;
        border-radius: 12px;
    }
    .stTextArea textarea {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# ======================
# 🧾 DUOMENŲ ĮVESTIS
# ======================
st.title("🪚 Kortų Optimizatorius (Mobilus)")

col1, col2 = st.columns(2)
with col1:
    uzsakymo_nr = st.text_input("Užsakymo numeris:", "UZS001")
with col2:
    plokstes_tipas = st.text_input("Plokštės tipas:", "MDF")

# Greiti šablonai
st.write("### Greiti šablonai plokštei:")
kortos_variantas = st.radio(
    "Pasirink kortos dydį:",
    ["2800x2070 (standartinė)", "3050x1830 (didelė)", "custom"],
    horizontal=True
)

if kortos_variantas == "custom":
    kortos_matmenys = st.text_input("Įvesk kortos matmenis:", "2800x2070")
else:
    kortos_matmenys = kortos_variantas.split(" ")[0]

try:
    kortos_ilgis, kortos_plotis = [int(x) for x in kortos_matmenys.lower().split("x")]
except:
    st.error("❌ Įvesk matmenis formatu: 2800x2070")
    st.stop()

# Ruošinių įvedimas
st.write("### Ruošiniai:")
default_pieces = "1200x800x5\n504x769\n1030x290\n1030x290\n1340x540\n1340x540\n788x700\n788x700"
raw_input = st.text_area("Įvesk ruošinius:", default_pieces, height=200)

# ======================
# 🔍 PARSINGAS
# ======================
def parse_pieces(text):
    pieces = []
    for line in text.strip().splitlines():
        if "x" not in line:
            continue
        parts = line.strip().split("x")
        try:
            if len(parts) == 3:
                w, h, qty = map(int, parts)
            elif len(parts) == 2:
                w, h = map(int, parts)
                qty = 1
            else:
                continue
            for _ in range(qty):
                pieces.append((w, h))
        except:
            st.warning(f"Klaida eilutėje: {line}")
    return pieces

pieces = parse_pieces(raw_input)

# ======================
# 🧠 PAPRASTAS OPTIMIZATORIUS
# ======================
def simple_layout(pieces, board_w, board_h):
    """Labai paprastas, stabilus išdėstymo algoritmas (ne guillotine)"""
    boards = []
    current_board = []
    x = y = max_height = 0

    for (w, h) in pieces:
        rotated = False
        if w > h and h <= board_w and w <= board_h:
            w, h = h, w
            rotated = True
        if x + w > board_w:
            x = 0
            y += max_height
            max_height = 0
        if y + h > board_h:
            boards.append(current_board)
            current_board = []
            x = y = max_height = 0
        current_board.append((x, y, w, h, rotated))
        x += w
        max_height = max(max_height, h)
    if current_board:
        boards.append(current_board)
    return boards

# ======================
# 🖼️ VIZUALIZACIJA
# ======================
def draw_board(board, width, height, title):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=12)

    for (x, y, w, h, rotated) in board:
        rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='black', facecolor='#AEDFF7')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, f"{w}×{h}", ha='center', va='center', fontsize=8)
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

# ======================
# 🧾 PDF GENERATORIUS
# ======================
def generate_pdf(boards, width, height, uzsakymo_nr, plokstes_tipas):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    scale = min((A4[0] - 60 * mm) / width, (A4[1] - 60 * mm) / height)
    for i, board in enumerate(boards, 1):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30 * mm, A4[1] - 30 * mm, f"{uzsakymo_nr} – Korta {i} ({plokstes_tipas})")
        for (x, y, w, h, _) in board:
            sx = 30 * mm + x * scale
            sy = 30 * mm + y * scale
            sw = w * scale
            sh = h * scale
            c.rect(sx, sy, sw, sh)
            c.setFont("Helvetica", 8)
            c.drawCentredString(sx + sw / 2, sy + sh / 2, f"{w}×{h}")
        c.showPage()
    c.save()
    buf.seek(0)
    return buf

# ======================
# 🚀 VEIKSMAS
# ======================
if st.button("🚀 GENERUOTI IŠDĖSTYMĄ IR PDF"):
    if not pieces:
        st.warning("Įvesk bent vieną ruošinį.")
    else:
        boards = simple_layout(pieces, kortos_ilgis, kortos_plotis)
        st.success(f"✅ Sugeneruota {len(boards)} kortų")

        for i, board in enumerate(boards, 1):
            st.markdown(f"### 📄 Korta {i}")
            fig = draw_board(board, kortos_ilgis, kortos_plotis, f"Korta {i}")
            st.pyplot(fig)
            plt.close(fig)

        pdf_buf = generate_pdf(boards, kortos_ilgis, kortos_plotis, uzsakymo_nr, plokstes_tipas)
        st.download_button(
            label="📥 Atsisiųsti PDF",
            data=pdf_buf,
            file_name=f"{uzsakymo_nr}.pdf",
            mime="application/pdf"
        )

# ======================
# ℹ️ ŠONINĖ INFO
# ======================
st.sidebar.header("📊 Statistika")
if pieces:
    piece_counts = Counter(pieces)
    for (w, h), count in piece_counts.items():
        st.sidebar.write(f"{w}×{h}: {count} vnt.")

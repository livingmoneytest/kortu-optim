import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image, Spacer
from reportlab.lib.pagesizes import landscape, A4
import tempfile
import io
import math
from collections import Counter

# ======================
# 📱 MOBILUS DIZAINAS
# ======================
st.set_page_config(page_title="Optimalus kortų optimizatorius", layout="centered")

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
        border-radius: 10px;
    }
    .stTextArea textarea {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# ======================
# 🪚 PAGRINDINĖ ANTRAŠTĖ
# ======================
st.title("🪚 Optimalus kortų optimizatorius (mobilus)")
st.write("Automatinis ruošinių išdėstymas pagal optimalius layout'us")

# ======================
# 🔢 DUOMENŲ ĮVESTIS
# ======================
col1, col2 = st.columns(2)
with col1:
    uzsakymo_nr = st.text_input("Užsakymo numeris:", "UZS001")
with col2:
    plokstes_tipas = st.text_input("Plokštės tipas:", "MDF")

st.write("### Greiti plokštės šablonai:")
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
    st.error("❌ Įvesk formatu: 2800x2070")
    st.stop()

st.write("### Įvesk ruošinius:")
raw_input = st.text_area(
    "Vienoje eilutėje – vienas ruošinys (pvz. 1200x800x5):",
    "1200x800x5\n504x769\n1030x290\n1340x540\n788x700\n290x1030\n222x700",
    height=200
)

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
# 🧠 OPTIMIZATORIAUS LOGIKA (TAVO VERSIJA)
# ======================
class OptimalPacker:
    def __init__(self, board_width, board_height):
        self.board_width = board_width
        self.board_height = board_height
        self.optimal_layouts = self._initialize_optimal_layouts()

    def _initialize_optimal_layouts(self):
        layouts = {}

        # 1200×800 optimalus layoutas
        layouts[(1200, 800)] = [
            (0, 0, 800, 1200, True),
            (800, 0, 800, 1200, True),
            (1600, 0, 800, 1200, True),
            (0, 1200, 1200, 800, False),
            (1200, 1200, 1200, 800, False)
        ]

        # 800×1200 optimalus layoutas
        layouts[(800, 1200)] = [
            (0, 0, 1200, 800, True),
            (1200, 0, 1200, 800, True),
            (0, 800, 800, 1200, False),
            (800, 800, 800, 1200, False),
            (1600, 800, 800, 1200, False)
        ]

        return layouts

    def pack_all_pieces(self, all_pieces):
        boards = []
        remaining_pieces = all_pieces.copy()
        optimized_pieces = []
        standard_pieces = []

        for piece in remaining_pieces:
            if piece in self.optimal_layouts:
                optimized_pieces.append(piece)
            else:
                standard_pieces.append(piece)

        boards.extend(self._pack_optimized_pieces(optimized_pieces))
        if standard_pieces:
            boards.extend(self._pack_standard_pieces(standard_pieces))
        return boards

    def _pack_optimized_pieces(self, optimized_pieces):
        boards = []
        piece_groups = {}
        for piece in optimized_pieces:
            if piece not in piece_groups:
                piece_groups[piece] = 0
            piece_groups[piece] += 1

        for piece_type, count in piece_groups.items():
            optimal_layout = self.optimal_layouts[piece_type]
            pieces_per_board = len(optimal_layout)
            full_boards = count // pieces_per_board
            remaining_pieces = count % pieces_per_board

            for _ in range(full_boards):
                boards.append({
                    'pieces': optimal_layout.copy(),
                    'free_rects': self._calculate_free_rectangles(optimal_layout),
                    'efficiency': self._calculate_efficiency(optimal_layout),
                    'type': f'optimal_{piece_type[0]}x{piece_type[1]}'
                })

            if remaining_pieces > 0:
                remaining_list = [piece_type] * remaining_pieces
                boards.extend(self._pack_standard_pieces(remaining_list))
        return boards

    def _pack_standard_pieces(self, standard_pieces):
        boards = []
        remaining_pieces = standard_pieces.copy()

        while remaining_pieces:
            board_pieces = []
            occupied_positions = []
            remaining_pieces.sort(key=lambda x: x[0] * x[1], reverse=True)

            for piece in remaining_pieces[:]:
                position = self._find_free_position_for_standard(piece, occupied_positions, board_pieces)
                if position:
                    x, y, w, h, rotated = position
                    board_pieces.append((x, y, w, h, rotated))
                    occupied_positions.append((x, y, x + w, y + h))
                    remaining_pieces.remove(piece)

            if board_pieces:
                boards.append({
                    'pieces': board_pieces,
                    'free_rects': self._calculate_free_rectangles(board_pieces),
                    'efficiency': self._calculate_efficiency(board_pieces),
                    'type': 'standard'
                })
            else:
                if remaining_pieces:
                    first_piece = remaining_pieces[0]
                    board_pieces = [(0, 0, first_piece[0], first_piece[1], False)]
                    boards.append({
                        'pieces': board_pieces,
                        'free_rects': self._calculate_free_rectangles(board_pieces),
                        'efficiency': self._calculate_efficiency(board_pieces),
                        'type': 'fallback'
                    })
                    remaining_pieces.remove(first_piece)
        return boards

    def _find_free_position_for_standard(self, piece, occupied_positions, existing_pieces):
        w, h = piece
        for orientation in [False, True]:
            if orientation:
                piece_width, piece_height = h, w
            else:
                piece_width, piece_height = w, h
            candidate_positions = [(0, 0)]
            for existing_x, existing_y, existing_w, existing_h, _ in existing_pieces:
                candidate_positions.append((existing_x + existing_w, existing_y))
                candidate_positions.append((existing_x, existing_y + existing_h))
            for x, y in candidate_positions:
                if x + piece_width <= self.board_width and y + piece_height <= self.board_height:
                    if not self._check_collision(x, y, piece_width, piece_height, occupied_positions):
                        return (x, y, piece_width, piece_height, orientation)
        return None

    def _check_collision(self, x, y, w, h, occupied_positions):
        new_rect = (x, y, x + w, y + h)
        for occupied in occupied_positions:
            ox1, oy1, ox2, oy2 = occupied
            if not (x + w <= ox1 or x >= ox2 or y + h <= oy1 or y >= oy2):
                return True
        return False

    def _calculate_free_rectangles(self, layout):
        if not layout:
            return [(0, 0, self.board_width, self.board_height)]
        max_height = 0
        for x, y, w, h, _ in layout:
            max_height = max(max_height, y + h)
        if max_height < self.board_height:
            return [(0, max_height, self.board_width, self.board_height - max_height)]
        return []

    def _calculate_efficiency(self, layout):
        if not layout:
            return 0
        used_area = sum(w * h for _, _, w, h, _ in layout)
        total_area = self.board_width * self.board_height
        return (used_area / total_area) * 100


# ======================
# 🎨 BRAIŽYMAS
# ======================
def draw_optimal_board(board_data, width, height, title):
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=14, fontweight='bold')

    pieces = board_data['pieces']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#87CEEB']

    for i, (x, y, w, h, rotated) in enumerate(pieces):
        color = colors[i % len(colors)]
        rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='darkblue', facecolor=color, alpha=0.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, f"{w}×{h}", ha='center', va='center', fontsize=8, fontweight='bold')

    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ======================
# 🧾 PDF GENERAVIMAS
# ======================


def generate_optimal_pdf(boards, width, height, uzsakymo_nr, plokstes_tipas):
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=landscape(A4))

    elements = []
    temp_images = []

    for i, board_data in enumerate(boards, 1):
        # Naudojame tą pačią vizualizaciją kaip ekrane
        fig = draw_optimal_board(board_data, width, height, f"{uzsakymo_nr} – Korta {i}")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.savefig(temp_file.name, bbox_inches='tight', dpi=150)
        plt.close(fig)

        # Įtraukiame į PDF
        elements.append(Image(temp_file.name, width=750, height=520))
        elements.append(Spacer(1, 12))
        temp_images.append(temp_file.name)

    pdf.build(elements)

    # Išvalome laikinus paveikslėlius
    for temp_path in temp_images:
        try:
            import os
            os.remove(temp_path)
        except:
            pass

    buf.seek(0)
    return buf



# ======================
# 🚀 PAGRINDINĖ LOGIKA
# ======================
if st.button("🚀 GENERUOTI OPTIMALŲ IŠDĖSTYMĄ"):
    if not pieces:
        st.warning("Įvesk bent vieną ruošinį.")
    else:
        with st.spinner("Kuriamas optimalus ruošinių išdėstymas..."):
            packer = OptimalPacker(kortos_ilgis, kortos_plotis)
            boards = packer.pack_all_pieces(pieces)

        st.subheader("📊 OPTIMALUS RUOŠINIŲ IŠDĖSTYMAS")

        total_pieces = sum(len(b['pieces']) for b in boards)
        total_used_area = sum(sum(w * h for _, _, w, h, _ in b['pieces']) for b in boards)
        total_area = kortos_ilgis * kortos_plotis * len(boards)
        overall_efficiency = total_used_area / total_area * 100

        for i, board_data in enumerate(boards, 1):
            st.write(f"### 📄 Korta {i} ({board_data['type']}) – {board_data['efficiency']:.1f}%")
            fig = draw_optimal_board(board_data, kortos_ilgis, kortos_plotis, f"Korta {i}")
            st.pyplot(fig)
            plt.close(fig)

        st.success(f"🎉 **Baigta! Bendra išeiga: {overall_efficiency:.1f}%**")
        pdf_buf = generate_optimal_pdf(boards, kortos_ilgis, kortos_plotis, uzsakymo_nr, plokstes_tipas)
        st.download_button("📥 Atsisiųsti PDF", pdf_buf, f"{uzsakymo_nr}_planas.pdf", "application/pdf")

# ======================
# ℹ️ ŠONINĖ INFO
# ======================
st.sidebar.header("📊 Statistika")
if pieces:
    piece_counts = Counter(pieces)
    for (w, h), count in piece_counts.items():
        st.sidebar.write(f"{w}×{h}: {count} vnt.")

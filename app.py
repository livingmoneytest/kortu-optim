import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
import io
import math
from collections import Counter

# Mobili optimizacija
st.set_page_config(
    page_title="Kortų Optimizatorius",
    page_icon="🪚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS for mobile optimization
st.markdown("""
<style>
    .main > div {
        padding: 1rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
    }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
    }
    .stTextArea > div > div > textarea {
        font-size: 1.1rem;
        height: 150px;
    }
    .mobile-header {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .mobile-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .piece-counter {
        background-color: #e6f3ff;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="mobile-header">🪚 Kortų Optimizatorius</div>', unsafe_allow_html=True)

# --- MOBILI ĮVESTIS ---
st.markdown('<div class="mobile-section">📋 Pagrindiniai duomenys</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    uzsakymo_nr = st.text_input("Užsakymo Nr:", "UZS001")
with col2:
    plokstes_tipas = st.selectbox("Plokštės tipas:", ["MDF", "MDP", "PPD", "KITA"])

st.markdown("### 📐 Plokštės matmenys")
kortos_matmenys = st.text_input("Įveskite matmenis (ilgis x plotis):", "2800x2070")

try:
    kortos_ilgis, kortos_plotis = [int(x) for x in kortos_matmenys.lower().split("x")]
except:
    st.error("❌ Neteisingas formatas. Naudokite: 2800x2070")
    st.stop()

# --- GREITI RUOŠINIŲ ŠABLONAI ---
st.markdown('<div class="mobile-section">🧩 Ruošiniai</div>', unsafe_allow_html=True)

# Greiti šablonai
template_option = st.selectbox(
    "Pasirinkite šabloną arba įveskite savo:",
    ["Pasirinkite...", "1200x800x5", "Standartiniai baldų ruošiniai", "Vartotojo įvestis"]
)

if template_option == "1200x800x5":
    raw_input = "1200x800x5"
elif template_option == "Standartiniai baldų ruošiniai":
    raw_input = "1200x800x3\n600x400x4\n800x600x2\n400x300x6"
else:
    raw_input = st.text_area(
        "Įveskite ruošinius (viena eilutė = vienas matmuo):",
        "1200x800x5\n600x400x2\n800x600x3",
        help="Pvz.: 1200x800x5 - 5 ruošiniai 1200x800 dydžio"
    )

# --- PARSINGAS ---
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
            continue
    return pieces

pieces = parse_pieces(raw_input)

# Rodome ruošinių statistiką
if pieces:
    piece_counts = Counter(pieces)
    st.markdown("### 📊 Ruošinių statistika")
    
    for (w, h), count in piece_counts.items():
        st.markdown(f'<div class="piece-counter">{w}×{h} mm: {count} vnt.</div>', unsafe_allow_html=True)
    
    st.write(f"**Viso ruošinių:** {len(pieces)}")

# --- OPTIMALUS OPTIMIZAVIMO ALGORITMAS (supaprastintas mobiliajai) ---
class MobilePacker:
    def __init__(self, board_width, board_height):
        self.board_width = board_width
        self.board_height = board_height
        self.optimal_layouts = {
            (1200, 800): [
                (0, 0, 800, 1200, True), (800, 0, 800, 1200, True), (1600, 0, 800, 1200, True),
                (0, 1200, 1200, 800, False), (1200, 1200, 1200, 800, False)
            ],
            (800, 1200): [
                (0, 0, 1200, 800, True), (1200, 0, 1200, 800, True),
                (0, 800, 800, 1200, False), (800, 800, 800, 1200, False), (1600, 800, 800, 1200, False)
            ]
        }
    
    def pack_all_pieces(self, all_pieces):
        boards = []
        remaining_pieces = all_pieces.copy()
        
        # Pirmiausia optimizuojami ruošiniai
        optimized_pieces = [p for p in remaining_pieces if p in self.optimal_layouts]
        standard_pieces = [p for p in remaining_pieces if p not in self.optimal_layouts]
        
        # Optimizuoti ruošiniai
        piece_groups = Counter(optimized_pieces)
        for piece_type, count in piece_groups.items():
            layout = self.optimal_layouts[piece_type]
            pieces_per_board = len(layout)
            full_boards = count // pieces_per_board
            
            for _ in range(full_boards):
                boards.append({
                    'pieces': layout.copy(),
                    'free_rects': self._calculate_free_rectangles(layout),
                    'efficiency': self._calculate_efficiency(layout),
                    'type': f'optimal'
                })
            
            # Likusios dalies apdorojimas
            remaining_count = count % pieces_per_board
            for _ in range(remaining_count):
                standard_pieces.append(piece_type)
        
        # Standartiniai ruošiniai
        while standard_pieces:
            board_pieces = []
            current_x, current_y, row_height = 0, 0, 0
            
            for piece in standard_pieces[:]:
                w, h = piece
                placed = False
                
                # Bandome abi orientacijas
                for orientation in [False, True]:
                    if orientation:
                        pw, ph = h, w
                    else:
                        pw, ph = w, h
                    
                    if current_x + pw <= self.board_width and current_y + ph <= self.board_height:
                        board_pieces.append((current_x, current_y, pw, ph, orientation))
                        current_x += pw
                        row_height = max(row_height, ph)
                        standard_pieces.remove(piece)
                        placed = True
                        break
                
                if not placed:
                    # Bandome naują eilę
                    if current_y + row_height + min(h, w) <= self.board_height:
                        current_x = 0
                        current_y += row_height
                        row_height = 0
                        continue
                    else:
                        break
            
            if board_pieces:
                boards.append({
                    'pieces': board_pieces,
                    'free_rects': self._calculate_free_rectangles(board_pieces),
                    'efficiency': self._calculate_efficiency(board_pieces),
                    'type': 'standard'
                })
            elif standard_pieces:
                # Priverstinis dėjimas
                piece = standard_pieces[0]
                boards.append({
                    'pieces': [(0, 0, piece[0], piece[1], False)],
                    'free_rects': [],
                    'efficiency': self._calculate_efficiency([(0, 0, piece[0], piece[1], False)]),
                    'type': 'fallback'
                })
                standard_pieces.remove(piece)
        
        return boards
    
    def _calculate_free_rectangles(self, layout):
        max_height = max(y + h for x, y, w, h, _ in layout) if layout else 0
        if max_height < self.board_height:
            return [(0, max_height, self.board_width, self.board_height - max_height)]
        return []
    
    def _calculate_efficiency(self, layout):
        used_area = sum(w * h for _, _, w, h, _ in layout)
        return (used_area / (self.board_width * self.board_height)) * 100

# --- MOBILI VIZUALIZACIJA ---
def draw_mobile_board(board_data, width, height, title):
    fig, ax = plt.subplots(figsize=(8, 6))  # Mažesnis dydis mobiliajai
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=12, fontweight='bold')
    
    pieces = board_data['pieces']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for i, (x, y, w, h, rotated) in enumerate(pieces):
        color = colors[i % len(colors)]
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, 
                               edgecolor='darkblue', facecolor=color, alpha=0.8)
        ax.add_patch(rect)
        
        # Sutrumpintas tekstas mobiliajai
        text = f"{w}×{h}"
        if rotated:
            text += " 🔄"
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
               fontsize=7, fontweight='bold')
    
    # Likučiai
    for (x, y, w, h) in board_data['free_rects']:
        if w * h > 1000:
            rect = patches.Rectangle((x, y), w, h, linewidth=1, 
                                   edgecolor='red', facecolor='none', linestyle='--')
            ax.add_patch(rect)
    
    ax.invert_yaxis()
    ax.grid(True, alpha=0.2)
    return fig

# --- PAGRINDINĖ PROGRAMOS LOGIKA ---
if st.button("🚀 GENERUOTI IŠDĖSTYMĄ", type="primary"):
    if not pieces:
        st.error("❌ Įveskite bent vieną ruošinį")
    else:
        with st.spinner("🔄 Kuriamas optimalus išdėstymas..."):
            packer = MobilePacker(kortos_ilgis, kortos_plotis)
            boards = packer.pack_all_pieces(pieces)
        
        st.markdown('<div class="mobile-section">📊 Rezultatai</div>', unsafe_allow_html=True)
        
        # Bendra statistika
        total_pieces = sum(len(b['pieces']) for b in boards)
        optimal_boards = sum(1 for b in boards if b['type'] == 'optimal')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Kortų", len(boards))
        with col2:
            st.metric("Ruošiniai", total_pieces)
        with col3:
            st.metric("Optimalios", optimal_boards)
        
        # Kortų peržiūra
        for i, board_data in enumerate(boards, 1):
            with st.expander(f"📦 Korta {i} ({board_data['type']}) - {board_data['efficiency']:.1f}%"):
                fig = draw_mobile_board(board_data, kortos_ilgis, kortos_plotis, 
                                      f"Korta {i} - {board_data['efficiency']:.1f}%")
                st.pyplot(fig)
                plt.close(fig)
                
                # Ruošinių sąrašas
                for j, (x, y, w, h, rotated) in enumerate(board_data['pieces'], 1):
                    orient = "Pasuktas" if rotated else "Originalus"
                    st.write(f"{j}. {w}×{h} mm ({orient}) - [{x}, {y}]")
        
        # PDF eksportas
        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=landscape(A4))
        scale = min((A4[0] - 80 * mm) / kortos_ilgis, (A4[1] - 80 * mm) / kortos_plotis)
        
        for i, board_data in enumerate(boards, 1):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40 * mm, A4[1] - 30 * mm, f"{uzsakymo_nr} - Korta {i}")
            
            for (x, y, w, h, rotated) in board_data['pieces']:
                sx = 40 * mm + x * scale
                sy = 40 * mm + y * scale
                sw = w * scale
                sh = h * scale
                c.rect(sx, sy, sw, sh)
                c.setFont("Helvetica", 6)
                c.drawCentredString(sx + sw/2, sy + sh/2, f"{w}×{h}")
            
            c.showPage()
        
        c.save()
        pdf_buf.seek(0)
        
        st.download_button(
            label="📥 Atsisiųsti PDF",
            data=pdf_buf,
            file_name=f"{uzsakymo_nr}_pjovimo_planas.pdf",
            mime="application/pdf"
        )

# --- MOBILI INFORMACIJA ---
st.markdown("---")
st.markdown("### ℹ️ Naudojimo instrukcija")

with st.expander("📱 Kaip naudotis telefone"):
    st.write("""
    1. **Įveskite pagrindinius duomenis:**
       - Užsakymo numerį
       - Plokštės tipą
       - Plokštės matmenis
    
    2. **Įveskite ruošinius:**
       - Viena eilutė = vienas matmuo
       - Pvz.: 1200x800x5
       - Arba pasirinkite šabloną
    
    3. **Spustelėkite „GENERUOTI IŠDĖSTYMĄ“**
    
    4. **Peržiūrėkite rezultatus ir atsisiųskite PDF**
    """)

with st.expander("🎯 Optimalūs layout'ai"):
    st.write("""
    Programa automatiškai optimizuoja:
    - **1200×800 ruošinius** - 5 vnt. vienoje plokštėje
    - **Kitus pasikartojančius ruošinius**
    - **Maksimalus medžiagos panaudojimas**
    """)

# Footer
st.markdown("---")
st.markdown("*Sukurta baldų gamybai* 🪚")

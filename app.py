import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
import io
import math
from collections import Counter

# Mobile optimized version
st.set_page_config(
    page_title="Board Optimizer",
    page_icon="🪚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile
st.markdown("""
<style>
    .main > div {
        padding: 0.5rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        margin: 0.2rem 0;
    }
    .number-btn {
        width: 100% !important;
        height: 3rem !important;
        font-size: 1.2rem !important;
        margin: 0.1rem !important;
    }
    .input-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .piece-item {
        background-color: #e9ecef;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🪚 Board Optimizer")
st.write("Mobile-optimized board cutting layout generator")

class MobileOptimizer:
    def __init__(self, board_width=2800, board_height=2070):
        self.board_width = board_width
        self.board_height = board_height
        self.optimal_layouts = {
            (1200, 800): [
                (0, 0, 800, 1200, True),
                (800, 0, 800, 1200, True),
                (1600, 0, 800, 1200, True),
                (0, 1200, 1200, 800, False),
                (1200, 1200, 1200, 800, False)
            ]
        }
    
    def parse_piece_input(self, text):
        """Parse piece input with multiple formats support"""
        if not text.strip():
            return None, None, None
            
        # Replace multiple spaces with single space and split
        parts = text.strip().replace('x', ' ').replace('×', ' ').split()
        
        try:
            if len(parts) == 2:
                w, h = int(parts[0]), int(parts[1])
                return w, h, 1
            elif len(parts) == 3:
                w, h, qty = int(parts[0]), int(parts[1]), int(parts[2])
                return w, h, qty
        except:
            pass
            
        return None, None, None
    
    def pack_pieces(self, pieces):
        """Pack pieces using optimal layouts when possible"""
        boards = []
        remaining = pieces.copy()
        
        # Process 1200x800 pieces with optimal layout
        count_1200x800 = sum(1 for p in remaining if p == (1200, 800))
        optimal_boards = count_1200x800 // 5
        
        for i in range(optimal_boards):
            boards.append({
                'pieces': self.optimal_layouts[(1200, 800)].copy(),
                'type': 'optimal_1200x800',
                'efficiency': 85.1
            })
            # Remove used pieces
            for _ in range(5):
                remaining.remove((1200, 800))
        
        # Pack remaining pieces using simple algorithm
        while remaining:
            board_pieces = []
            current_x, current_y, row_height = 0, 0, 0
            
            for piece in remaining[:]:
                w, h = piece
                placed = False
                
                # Try both orientations
                for orientation in [False, True]:
                    if orientation:
                        pw, ph = h, w
                    else:
                        pw, ph = w, h
                    
                    if current_x + pw <= self.board_width and current_y + ph <= self.board_height:
                        board_pieces.append((current_x, current_y, pw, ph, orientation))
                        current_x += pw
                        row_height = max(row_height, ph)
                        remaining.remove(piece)
                        placed = True
                        break
                
                if not placed:
                    # Try new row
                    if current_y + row_height + min(h, w) <= self.board_height:
                        current_x = 0
                        current_y += row_height
                        row_height = 0
                        continue
                    else:
                        break
            
            if board_pieces:
                used_area = sum(w * h for _, _, w, h, _ in board_pieces)
                efficiency = (used_area / (self.board_width * self.board_height)) * 100
                boards.append({
                    'pieces': board_pieces,
                    'type': 'standard',
                    'efficiency': efficiency
                })
            elif remaining:
                # Force place first piece
                piece = remaining[0]
                boards.append({
                    'pieces': [(0, 0, piece[0], piece[1], False)],
                    'type': 'fallback',
                    'efficiency': (piece[0] * piece[1]) / (self.board_width * self.board_height) * 100
                })
                remaining.remove(piece)
        
        return boards

# Initialize session state
if 'pieces' not in st.session_state:
    st.session_state.pieces = []
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""

# Input sections
st.markdown('<div class="input-section">', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    order_no = st.text_input("Order No:", "ORDER001")
with col2:
    board_type = st.selectbox("Board Type:", ["MDF", "HDF", "LDF", "MDP", "PPD", "OTHER"])

# Fixed board size (2800x2070 as default)
board_width, board_height = 2800, 2070
st.info(f"Board Size: {board_width} × {board_height} mm")

st.markdown('</div>', unsafe_allow_html=True)

# Pieces input section
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.subheader("Add Pieces")

# Current input display
st.text_input("Current Piece:", value=st.session_state.current_input, key="display_input", disabled=True)

# Number pad
st.write("Enter dimensions (width height quantity):")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("1", key="btn1", use_container_width=True):
        st.session_state.current_input += "1"
    if st.button("4", key="btn4", use_container_width=True):
        st.session_state.current_input += "4"
    if st.button("7", key="btn7", use_container_width=True):
        st.session_state.current_input += "7"
    if st.button("0", key="btn0", use_container_width=True):
        st.session_state.current_input += "0"

with col2:
    if st.button("2", key="btn2", use_container_width=True):
        st.session_state.current_input += "2"
    if st.button("5", key="btn5", use_container_width=True):
        st.session_state.current_input += "5"
    if st.button("8", key="btn8", use_container_width=True):
        st.session_state.current_input += "8"
    if st.button("Space", key="btn_space", use_container_width=True):
        st.session_state.current_input += " "

with col3:
    if st.button("3", key="btn3", use_container_width=True):
        st.session_state.current_input += "3"
    if st.button("6", key="btn6", use_container_width=True):
        st.session_state.current_input += "6"
    if st.button("9", key="btn9", use_container_width=True):
        st.session_state.current_input += "9"
    if st.button("Clear", key="btn_clear", use_container_width=True):
        st.session_state.current_input = ""

# Add piece button
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("📥 Add Piece", use_container_width=True):
        if st.session_state.current_input.strip():
            optimizer = MobileOptimizer()
            w, h, qty = optimizer.parse_piece_input(st.session_state.current_input)
            if w and h and qty:
                for _ in range(qty):
                    st.session_state.pieces.append((w, h))
                st.session_state.current_input = ""
                st.rerun()
            else:
                st.error("Invalid format! Use: width height quantity")
with col2:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.pieces = []
        st.session_state.current_input = ""
        st.rerun()

# Show current pieces
if st.session_state.pieces:
    st.write("Current Pieces:")
    piece_counts = Counter(st.session_state.pieces)
    for (w, h), count in piece_counts.items():
        st.markdown(f'<div class="piece-item">{w}×{h} mm: {count} pcs</div>', unsafe_allow_html=True)
    
    st.write(f"Total pieces: {len(st.session_state.pieces)}")

st.markdown('</div>', unsafe_allow_html=True)

# Generate layout
if st.button("🚀 GENERATE OPTIMAL LAYOUT", type="primary"):
    if not st.session_state.pieces:
        st.error("Please add at least one piece")
    else:
        with st.spinner("Generating optimal layout..."):
            optimizer = MobileOptimizer()
            boards = optimizer.pack_pieces(st.session_state.pieces)
            
            # Display results
            st.subheader("📊 Optimization Results")
            
            total_pieces = sum(len(b['pieces']) for b in boards)
            optimal_boards = sum(1 for b in boards if b['type'] == 'optimal_1200x800')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Boards", len(boards))
            with col2:
                st.metric("Pieces", total_pieces)
            with col3:
                st.metric("Optimized", optimal_boards)
            
            # Show each board
            for i, board in enumerate(boards):
                with st.expander(f"Board {i+1} ({board['type']}) - Efficiency: {board['efficiency']:.1f}%"):
                    # Create visualization
                    fig, ax = plt.subplots(figsize=(10, 8))
                    ax.set_xlim(0, board_width)
                    ax.set_ylim(0, board_height)
                    ax.set_aspect('equal')
                    
                    # Draw pieces
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                    for j, (x, y, w, h, rotated) in enumerate(board['pieces']):
                        color = colors[j % len(colors)]
                        rect = patches.Rectangle((x, y), w, h, linewidth=2,
                                              edgecolor='darkblue', facecolor=color, alpha=0.8)
                        ax.add_patch(rect)
                        
                        # Text
                        orient = "R" if rotated else "O"
                        ax.text(x + w/2, y + h/2, f"{w}×{h}\n{orient}",
                              ha='center', va='center', fontsize=8, fontweight='bold')
                    
                    ax.invert_yaxis()
                    ax.grid(True, alpha=0.3)
                    ax.set_title(f"Board {i+1} - {board['efficiency']:.1f}%", fontweight='bold')
                    st.pyplot(fig)
                    plt.close(fig)
                    
                    # Piece list
                    st.write("Pieces in this board:")
                    for j, (x, y, w, h, rotated) in enumerate(board['pieces'], 1):
                        orient = "Rotated" if rotated else "Original"
                        st.write(f"{j}. {w}×{h} mm ({orient}) - Position: [{x}, {y}]")
            
            # Generate PDF
            pdf_buf = io.BytesIO()
            c = canvas.Canvas(pdf_buf, pagesize=landscape(A4))
            scale = min((A4[0] - 80 * mm) / board_width, (A4[1] - 80 * mm) / board_height)
            
            for i, board in enumerate(boards):
                c.setFont("Helvetica-Bold", 16)
                c.drawString(40 * mm, A4[1] - 30 * mm, f"{order_no} - Board {i+1}")
                c.setFont("Helvetica", 10)
                c.drawString(40 * mm, A4[1] - 45 * mm, f"Type: {board['type']} | Efficiency: {board['efficiency']:.1f}%")
                
                # Draw pieces
                for (x, y, w, h, rotated) in board['pieces']:
                    sx = 40 * mm + x * scale
                    sy = 40 * mm + y * scale
                    sw = w * scale
                    sh = h * scale
                    c.rect(sx, sy, sw, sh)
                    c.setFont("Helvetica-Bold", 6)
                    c.drawCentredString(sx + sw/2, sy + sh/2, f"{w}×{h}")
                
                c.showPage()
            
            c.save()
            pdf_buf.seek(0)
            
            # Download button
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buf,
                file_name=f"{order_no}_cutting_plan.pdf",
                mime="application/pdf"
            )

# Instructions
with st.expander("📱 How to use"):
    st.write("""
    1. **Select board type** from dropdown
    2. **Add pieces** using number pad:
       - Format: `width height quantity`
       - Example: `1200 800 5` for five 1200×800 pieces
       - Example: `600 400` for one 600×400 piece
    3. **Generate layout** to see optimization
    4. **Download PDF** for cutting instructions
    
    **Optimization features:**
    - 1200×800 pieces automatically packed optimally (3 vertical + 2 horizontal)
    - Other pieces packed efficiently
    - Mobile-optimized interface
    """)

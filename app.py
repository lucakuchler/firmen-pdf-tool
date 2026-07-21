import streamlit as st
import google.generativeai as genai
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Firmen PDF Generator", page_icon="📄", layout="centered")

st.title("📄 Firmen PDF Generator")
st.write("Füge Daten ein, um das PDF automatisch zu füllen.")

# --- API KEY AUTOMATISCH ODER MANUELL ---
# Versucht den Key zuerst aus den Streamlit Secrets zu laden
api_key = st.secrets.get("GEMINI_API_KEY", "")

# Falls kein Key in den Secrets hinterlegt ist, Sidebar-Eingabe als Backup nutzen
if not api_key:
    st.sidebar.header("Einstellungen")
    api_key = st.sidebar.text_input("Google AI Studio API-Key:", type="password")

# --- MAIN INPUT ---
user_input = st.text_area(
    "Geben Sie hier die Daten oder Anweisungen ein:", 
    height=150, 
    placeholder="Z. B. 'Außenkreis Scheiben 5, Radius 10...'"
)

# --- MODELL-VERARBEITUNG ---
def generate_values_with_gemini(api_key, user_text):
    genai.configure(api_key=api_key)
    
    models_to_try = ["gemini-3.5-flash", "gemini-flash-latest"]
    
    prompt = f"""
    Du bist ein Präzisions-Tool zur Datenextraktion.
    Verarbeite folgenden Text und liefere EXAKT 4 Zahlen/Werte in folgender Reihenfolge zurück:
    1. Scheibenanzahl AUSSEN-KREIS
    2. Radius AUSSEN-KREIS
    3. Radius INNEN-KREIS
    4. Scheibenanzahl INNEN-KREIS
    
    Eingabetext:
    {user_text}

    Antworte AUSSCHLIESSLICH im Format: Wert1, Wert2, Wert3, Wert4
    Keine Erklärungen, kein Markdown, nur die 4 Werte durch Komma getrennt.
    """
    
    last_error = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            last_error = e
            continue
            
    raise last_error

# --- PROCESS BUTTON ---
if st.button("🚀 PDF Erstellen & Ausfüllen", type="primary"):
    if not api_key:
        st.error("Kein API-Key gefunden! Bitte hinterlege GEMINI_API_KEY in den Secrets oder gib ihn in der Sidebar ein.")
    elif not user_input.strip():
        st.warning("Bitte gib Daten oder Text ein.")
    else:
        status_box = st.empty()
        
        try:
            # 1. API Aufruf
            status_box.info("🧠 Extrahiere Werte mit Gemini...")
            raw_response = generate_values_with_gemini(api_key, user_input)
            
            # Werte parsen
            werte = [w.strip() for w in raw_response.split(",")]
            while len(werte) < 4:
                werte.append("0")

            status_box.empty()
            st.info(f"📍 Erkannte Werte (Außen-Anz, Außen-Rad, Innen-Rad, Innen-Anz): {', '.join(werte[:4])}")

            # 2. PDF Overlay erstellen
            status_box.info("📄 Erstelle PDF-Datei...")
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=A4)
            c.setFont("Helvetica-Bold", 12)
            
            # --- KOORDINATEN DER 4 BOXEN ---
            Y_POS = 450  # Höhe der Boxen auf der Seite
            
            X_SCHA_AUSSEN = 300  # 1. Scheibenanzahl AUSSEN-KREIS
            X_RAD_AUSSEN  = 360  # 2. Radius AUSSEN-KREIS
            X_RAD_INNEN   = 420  # 3. Radius INNEN-KREIS
            X_SCHA_INNEN  = 480  # 4. Scheibenanzahl INNEN-KREIS

            c.drawString(X_SCHA_AUSSEN, Y_POS, werte[0])
            c.drawString(X_RAD_AUSSEN,  Y_POS, werte[1])
            c.drawString(X_RAD_INNEN,   Y_POS, werte[2])
            c.drawString(X_SCHA_INNEN,  Y_POS, werte[3])
            
            c.save()
            packet.seek(0)

            # 3. Mit Vorlage.pdf zusammenführen
            overlay_pdf = PdfReader(packet)
            original_pdf = PdfReader("Vorlage.pdf")
            writer = PdfWriter()

            first_page = original_pdf.pages[0]
            first_page.merge_page(overlay_pdf.pages[0])
            writer.add_page(first_page)

            for page in original_pdf.pages[1:]:
                writer.add_page(page)

            output_pdf = io.BytesIO()
            writer.write(output_pdf)
            output_pdf.seek(0)

            status_box.empty()
            st.success("✅ PDF wurde erfolgreich generiert!")
            
            # 4. Download Button
            st.download_button(
                label="📥 Fertiges PDF Herunterladen",
                data=output_pdf,
                file_name="ausgefuellt.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            status_box.empty()
            st.error(f"❌ Fehler bei der Ausführung: {e}")

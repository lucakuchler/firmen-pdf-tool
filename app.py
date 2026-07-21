import streamlit as st
from google import genai
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- SEITEN-LAYOUT ---
st.set_page_config(page_title="Firmen PDF Generator", layout="centered")
st.title("📄 Firmen PDF Generator")

# API-Key Eingabe in der Seitenleiste
api_key = st.sidebar.text_input("Gemini API-Key eingeben:", type="password")

# Textfeld für den Nutzer
user_input = st.text_area("Geben Sie hier die Anweisungen oder Daten für die KI ein:", height=150)

if st.button("PDF Erstellen & Ausfüllen"):
    if not api_key:
        st.error("Bitte gib zuerst deinen Gemini API-Key in der linken Seitenleiste ein!")
    elif not user_input:
        st.warning("Bitte gib einen Text oder Daten ein.")
    else:
        with st.spinner("Gemini berechnet die Werte und baut die PDF..."):
            try:
                # 1. Gemini KI aufrufen
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Extrahiere oder berechne aus folgendem Text genau 4 Werte. Gib NUR die 4 Werte kommagetrennt zurück, sonst nichts:\n\n{user_input}"
                )
                
                # 2. Werte aufteilen
                werte = [w.strip() for w in response.text.split(",")]
                while len(werte) < 4:
                    werte.append("0")

                # 3. Transparente Zahlenseite im Hintergrund erzeugen
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.setFont("Helvetica-Bold", 12)
                c.setFillColorRGB(0, 0, 0) # Schwarze Schrift
                
                # =========================================================
                # HIER KOORDINATEN ANPASSEN (X = von links, Y = von unten)
                # =========================================================
                c.drawString(100, 700, werte[0])  # Zahl 1
                c.drawString(100, 650, werte[1])  # Zahl 2
                c.drawString(100, 600, werte[2])  # Zahl 3
                c.drawString(100, 550, werte[3])  # Zahl 4
                
                c.save()
                packet.seek(0)

                # 4. Transparente Zahlen auf die Original-PDF stempeln
                zahlen_pdf = PdfReader(packet)
                original_pdf = PdfReader("vorlage.pdf")
                writer = PdfWriter()

                page = original_pdf.pages[0]
                page.merge_page(zahlen_pdf.pages[0])
                writer.add_page(page)

                # Weitere Seiten der Vorlage übernehmen (falls vorhanden)
                for p in original_pdf.pages[1:]:
                    writer.add_page(p)

                output_pdf = io.BytesIO()
                writer.write(output_pdf)
                output_pdf.seek(0)

                # 5. Erfolgsmeldung & Download-Button
                st.success("PDF erfolgreich generiert!")
                st.download_button(
                    label="📥 Fertige PDF herunterladen",
                    data=output_pdf,
                    file_name="ausgefuellt.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Fehler bei der Generierung: {e}")

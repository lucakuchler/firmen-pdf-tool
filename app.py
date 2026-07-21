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

# Textfeld für die Nutzereingabe
user_input = st.text_area("Geben Sie hier die Daten oder Anweisungen ein:", height=150)

if st.button("PDF Erstellen & Ausfüllen"):
    if not api_key:
        st.error("Bitte gib zuerst deinen Gemini API-Key in der linken Seitenleiste ein!")
    elif not user_input:
        st.warning("Bitte gib einen Text oder Daten ein.")
    else:
        with st.spinner("Gemini berechnet die Werte und baut die PDF..."):
            try:
                # 1. Gemini Client initialisieren
                client = genai.Client(api_key=api_key)
                
                # Automatisch verfügbare Modelle für deinen API-Key abfragen
                available_models = [m.name for m in client.models.list()]
                
                # Suche nach echten, gültigen Modellen in Prioritätsreihenfolge
                selected_model = None
                for candidate in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
                    for m in available_models:
                        if candidate in m:
                            selected_model = m
                            break
                    if selected_model:
                        break
                
                # Fallback, falls die Namen anders formatiert sind
                if not selected_model and available_models:
                    selected_model = available_models[0]

                prompt = f"""
                Du bist ein hochpräzises Firmen-Berechnungs-Tool. 
                Verarbeite folgende Eingabe basierend auf der Firmen-Logik:
                {user_input}
                
                WICHTIG: Gib am Ende AUSSCHLIESSLICH genau 4 kommagetrennte Werte/Zahlen zurück, sonst keinerlei weiteren Text.
                Beispiel: 1250.00, 19%, 237.50, 1487.50
                """

                # Aufruf mit dem dynamisch ermittelten Modell
                response = client.models.generate_content(
                    model=selected_model,
                    contents=prompt,
                )
                
                # 2. Berechnete Werte aufteilen
                werte = [w.strip() for w in response.text.split(",")]
                while len(werte) < 4:
                    werte.append("0")

                # 3. Transparente Zahlenseite im Hintergrund erzeugen
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.setFont("Helvetica-Bold", 12)
                c.setFillColorRGB(0, 0, 0)
                
                # KOORDINATEN FÜR DIE 4 ZAHLEN (X = von links, Y = von unten in Punkten)
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

                # Weitere Seiten übernehmen
                for p in original_pdf.pages[1:]:
                    writer.add_page(p)

                output_pdf = io.BytesIO()
                writer.write(output_pdf)
                output_pdf.seek(0)

                # 5. Erfolgsmeldung & Download-Button
                st.success(f"PDF erfolgreich generiert! (Nutzt Modell: {selected_model})")
                st.download_button(
                    label="📥 Fertige PDF herunterladen",
                    data=output_pdf,
                    file_name="ausgefuellt.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Fehler bei der Generierung: {e}")

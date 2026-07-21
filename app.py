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
                # 1. Client initialisieren
                client = genai.Client(api_key=api_key)

                prompt = f"""
                Du bist ein hochpräzises Firmen-Berechnungs-Tool. 
                Verarbeite folgende Eingabe basierend auf der Firmen-Logik:
                {user_input}
                
                WICHTIG: Gib am Ende AUSSCHLIESSLICH genau 4 kommagetrennte Werte/Zahlen zurück, sonst keinerlei weiteren Text.
                Beispiel: 1250.00, 19%, 237.50, 1487.50
                """

                # Liste aller möglichen Modellbezeichnungen bei Google
                candidate_models = [
                    'gemini-1.5-flash-latest',
                    'gemini-2.5-flash',
                    'gemini-2.0-flash',
                    'gemini-1.5-flash-8b'
                ]

                response = None
                used_model = None
                last_error = None

                # Schleife: Probiere die Modelle der Reihe nach durch
                for model_name in candidate_models:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        used_model = model_name
                        break  # Erfolg! Schleife abbrechen
                    except Exception as err:
                        last_error = err
                        continue  # Bei Fehler das nächste Modell probieren

                if response is None:
                    raise Exception(f"Keines der verfügbaren Modelle konnte erreicht werden. Letzter Fehler: {last_error}")

                # 2. Berechnete Werte aufteilen
                werte = [w.strip() for w in response.text.split(",")]
                while len(werte) < 4:
                    werte.append("0")

                # 3. Transparente Zahlenseite im Hintergrund erzeugen
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.setFont("Helvetica-Bold", 12)
                c.setFillColorRGB(0, 0, 0)
                
                # KOORDINATEN FÜR DIE 4 ZAHLEN
                c.drawString(100, 700, werte[0])
                c.drawString(100, 650, werte[1])
                c.drawString(100, 600, werte[2])
                c.drawString(100, 550, werte[3])
                
                c.save()
                packet.seek(0)

                # 4. Transparente Zahlen auf die Original-PDF stempeln
                zahlen_pdf = PdfReader(packet)
                original_pdf = PdfReader("vorlage.pdf")
                writer = PdfWriter()

                page = original_pdf.pages[0]
                page.merge_page(zahlen_pdf.pages[0])
                writer.add_page(page)

                for p in original_pdf.pages[1:]:
                    writer.add_page(p)

                output_pdf = io.BytesIO()
                writer.write(output_pdf)
                output_pdf.seek(0)

                # 5. Erfolgsmeldung & Download-Button
                st.success(f"PDF erfolgreich generiert! (Verwendetes Modell: {used_model})")
                st.download_button(
                    label="📥 Fertige PDF herunterladen",
                    data=output_pdf,
                    file_name="ausgefuellt.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Fehler bei der Generierung: {e}")

import streamlit as st
import openai
import os
from PIL import Image
import pytesseract
import pdf2image
import fitz  # PyMuPDF
import speech_recognition as sr
from gtts import gTTS
import io
import base64
import tempfile
import nltk
from nltk.tokenize import sent_tokenize
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import json

# Configurazione pagina
st.set_page_config(
    page_title="AI-DSA Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'saved_texts' not in st.session_state:
    st.session_state.saved_texts = []
if 'reading_time' not in st.session_state:
    st.session_state.reading_time = 0
if 'simplified_texts' not in st.session_state:
    st.session_state.simplified_texts = {}

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4A6FA5;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
    }
    .highlight-text {
        background-color: #FFF9C4;
        padding: 0.2rem 0.5rem;
        border-radius: 3px;
        font-weight: bold;
    }
    .dyslexia-friendly {
        font-family: 'OpenDyslexic', 'Comic Sans MS', sans-serif;
        line-height: 1.8;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Barra laterale
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/brain.png", width=100)
    st.title("⚙️ Configurazione")
    
    st.subheader("🔑 API Keys")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    if openai_api_key:
        openai.api_key = openai_api_key
        st.success("✅ API Key configurata")
    
    st.divider()
    
    st.subheader("🎨 Personalizzazione")
    dyslexia_mode = st.checkbox("Attiva Font DSA-friendly")
    font_size = st.slider("Dimensione Font", 14, 24, 18)
    line_spacing = st.slider("Spaziatura Linee", 1.0, 2.5, 1.8)
    high_contrast = st.checkbox("Alto Contrasto")
    
    st.divider()
    
    st.subheader("📊 Statistiche")
    st.metric("Testi Salvati", len(st.session_state.saved_texts))
    st.metric("Minuti Letti", st.session_state.reading_time)
    
    if st.button("🗑️ Reset Statistiche"):
        st.session_state.saved_texts = []
        st.session_state.reading_time = 0
        st.rerun()

# Funzioni principali
def text_to_speech(text, language='it'):
    """Converte testo in audio"""
    tts = gTTS(text=text, lang=language, slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

def simplify_text(text):
    """Semplifica il testo usando OpenAI"""
    prompt = f"""
    Semplifica questo testo per uno studente con dislessia:
    1. Usa frasi brevi
    2. Evita parole complesse
    3. Aggiungi esempi concreti
    4. Suddividi in paragrafi brevi
    
    Testo originale:
    {text}
    
    Testo semplificato:
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un tutor specializzato nell'aiutare studenti con DSA."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Errore nella semplificazione: {str(e)}"

def extract_text_from_pdf(pdf_file):
    """Estrae testo da PDF"""
    try:
        # Metodo 1: PyMuPDF
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except:
        try:
            # Metodo 2: pdf2image + OCR
            images = pdf2image.convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang='ita')
            return text
        except Exception as e:
            return f"Errore nell'estrazione testo: {str(e)}"

def create_mind_map(text):
    """Crea una mappa concettuale dal testo"""
    prompt = f"""
    Crea una mappa concettuale gerarchica da questo testo.
    Formatta in questo modo:
    
    CONCETTO PRINCIPALE
    ├── Idea 1
    │   ├── Sottoidea A
    │   └── Sottoidea B
    ├── Idea 2
    └── Idea 3
    
    Testo:
    {text[:1000]}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Crea mappe concettuali chiare e strutturate."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except:
        return "Non posso creare la mappa concettuale senza API Key."

# Interfaccia principale
st.markdown('<h1 class="main-header">🧠 AI-DSA Assistant</h1>', unsafe_allow_html=True)
st.markdown("### Il tuo assistente intelligente per l'apprendimento inclusivo")

# Tab principali
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 Lettura Intelligente", 
    "🎤 Sintesi Vocale", 
    "🧩 Mappe Concettuali",
    "📚 Materiali",
    "📊 Progressi",
    "💡 Suggerimenti"
])

# TAB 1: Lettura Intelligente
with tab1:
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📄 Carica o Inserisci Testo")
        
        input_method = st.radio(
            "Scegli come inserire il testo:",
            ["📝 Digita", "📄 Carica PDF", "📸 Carica Immagine", "🎤 Registra Audio"]
        )
        
        text_input = ""
        
        if input_method == "📝 Digita":
            text_input = st.text_area(
                "Incolla il testo qui:",
                height=200,
                placeholder="Incolla il testo che vuoi semplificare..."
            )
        
        elif input_method == "📄 Carica PDF":
            pdf_file = st.file_uploader("Carica un PDF", type=['pdf'])
            if pdf_file:
                with st.spinner("Estrazione testo dal PDF..."):
                    text_input = extract_text_from_pdf(pdf_file)
                st.text_area("Testo estratto:", text_input, height=200)
        
        elif input_method == "📸 Carica Immagine":
            image_file = st.file_uploader("Carica un'immagine", type=['png', 'jpg', 'jpeg'])
            if image_file:
                image = Image.open(image_file)
                st.image(image, width=300)
                with st.spinner("Riconoscimento testo..."):
                    text_input = pytesseract.image_to_string(image, lang='ita')
                st.text_area("Testo riconosciuto:", text_input, height=200)
        
        elif input_method == "🎤 Registra Audio":
            st.info("Premi il pulsante e parla per 10 secondi")
            if st.button("🎙️ Inizia Registrazione"):
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=10)
                    try:
                        text_input = recognizer.recognize_google(audio, language="it-IT")
                        st.text_area("Testo trascritto:", text_input, height=200)
                    except sr.UnknownValueError:
                        st.error("Non ho capito l'audio")
                    except sr.RequestError:
                        st.error("Errore nel servizio di riconoscimento")
    
    with col2:
        st.subheader("🎯 Strumenti di Supporto")
        
        if text_input:
            # Calcola metriche
            sentences = sent_tokenize(text_input, language='italian')
            words = text_input.split()
            
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                st.metric("Parole", len(words))
            with col_metric2:
                st.metric("Frasi", len(sentences))
            
            # Strumenti
            if st.button("🔧 Semplifica Testo", use_container_width=True):
                with st.spinner("Semplificazione in corso..."):
                    simplified = simplify_text(text_input)
                    st.session_state.simplified_texts['ultimo'] = simplified
                    st.text_area("Testo Semplificato:", simplified, height=300)
            
            if st.button("🎧 Ascolta Testo", use_container_width=True):
                audio_file = text_to_speech(text_input)
                st.audio(audio_file, format='audio/mp3')
                st.session_state.reading_time += len(words) / 150  # 150 parole/minuto
            
            if st.button("💾 Salva per dopo", use_container_width=True):
                st.session_state.saved_texts.append({
                    'text': text_input[:100] + "...",
                    'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M"),
                    'word_count': len(words)
                })
                st.success("Testo salvato!")
            
            # Modalità lettura facilitata
            st.divider()
            if dyslexia_mode:
                st.markdown('<div class="dyslexia-friendly">', unsafe_allow_html=True)
            
            if high_contrast:
                st.markdown('<div style="background:black;color:white;padding:1rem;">', unsafe_allow_html=True)
            
            st.subheader("📖 Anteprima")
            preview_text = st.session_state.simplified_texts.get('ultimo', text_input)
            
            # Evidenzia parole complesse
            complex_words = ['tuttavia', 'pertanto', 'inoltre', 'dunque', 'comunque']
            for word in complex_words:
                if word in preview_text.lower():
                    preview_text = preview_text.replace(word, f'<span class="highlight-text">{word}</span>')
            
            st.markdown(preview_text[:500] + "...", unsafe_allow_html=True)
            
            if high_contrast:
                st.markdown('</div>', unsafe_allow_html=True)
            if dyslexia_mode:
                st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: Sintesi Vocale
with tab2:
    st.subheader("🔊 Sintesi Vocale e Registrazione")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Testo da Convertire")
        tts_text = st.text_area(
            "Inserisci testo per la sintesi vocale:",
            height=150,
            placeholder="Scrivi qui il testo che vuoi ascoltare..."
        )
        
        if tts_text:
            col_lang, col_speed = st.columns(2)
            with col_lang:
                language = st.selectbox("Lingua", ["it", "en", "es", "fr"])
            with col_speed:
                speed = st.slider("Velocità", 0.5, 1.5, 1.0)
            
            if st.button("🎵 Genera Audio", use_container_width=True):
                with st.spinner("Generazione audio in corso..."):
                    audio = text_to_speech(tts_text, language)
                    
                st.audio(audio, format='audio/mp3')
                
                # Download button
                st.download_button(
                    label="📥 Scarica Audio",
                    data=audio,
                    file_name="audio_dsa_assistant.mp3",
                    mime="audio/mp3"
                )
    
    with col2:
        st.markdown("### 🎙️ Registrazione Vocale")
        st.info("Registra appunti vocali da convertire in testo")
        
        if st.button("🎤 Inizia Nuova Registrazione", use_container_width=True):
            st.warning("Funzionalità da implementare con connessione microfono")
            
        st.divider()
        
        st.markdown("### 📋 Cronologia Audio")
        if st.session_state.saved_texts:
            for i, item in enumerate(st.session_state.saved_texts[-5:]):
                st.caption(f"{item['timestamp']} - {item['word_count']} parole")
                st.text(item['text'][:100] + "...")

# TAB 3: Mappe Concettuali
with tab3:
    st.subheader("🧠 Generatore di Mappe Concettuali")
    
    map_text = st.text_area(
        "Incolla il testo per generare la mappa concettuale:",
        height=150,
        placeholder="Incolla il testo del capitolo o argomento..."
    )
    
    if map_text and openai_api_key:
        if st.button("🌳 Genera Mappa Concettuale", use_container_width=True):
            with st.spinner("Creazione mappa concettuale..."):
                mind_map = create_mind_map(map_text)
            
            st.markdown("### 🎯 Mappa Concettuale Generata")
            
            # Visualizzazione come testo strutturato
            st.text_area("Struttura della mappa:", mind_map, height=300)
            
            # Opzioni di esportazione
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button("📥 Esporta come Immagine"):
                    st.info("Funzionalità avanzata - richiede librerie aggiuntive")
            with col_exp2:
                if st.button("📄 Esporta come Documento"):
                    st.info("Funzionalità avanzata - richiede librerie aggiuntive")
    
    elif not openai_api_key:
        st.warning("Inserisci la tua OpenAI API Key nella sidebar per usare questa funzione")

# TAB 4: Materiali
with tab4:
    st.subheader("📚 Libreria Materiali")
    
    # Esempi di materiali pre-caricati
    materials = {
        "Come Studiare con DSA": {
            "content": """1. Usa mappe mentali
2. Suddividi in sessioni brevi
3. Usa supporti visivi
4. Ripeti ad alta voce""",
            "type": "suggerimenti"
        },
        "Strumenti Compensativi": {
            "content": """• Sintesi vocale
• Mappe concettuali
• Calcolatrice parlante
• Tavola pitagorica""",
            "type": "lista"
        }
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📖 Materiali Disponibili")
        for title, material in materials.items():
            with st.expander(f"📄 {title}"):
                st.write(material["content"])
                if st.button(f"🎧 Ascolta {title}", key=f"audio_{title}"):
                    audio = text_to_speech(material["content"])
                    st.audio(audio, format='audio/mp3')
    
    with col2:
        st.markdown("### ✍️ Crea Nuovo Materiale")
        
        new_title = st.text_input("Titolo del materiale:")
        new_content = st.text_area("Contenuto:", height=150)
        
        if st.button("💾 Salva Materiale", use_container_width=True):
            if new_title and new_content:
                materials[new_title] = {
                    "content": new_content,
                    "type": "custom",
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.success(f"Materiale '{new_title}' salvato!")

# TAB 5: Progressi
with tab5:
    st.subheader("📊 Monitoraggio Progressi")
    
    # Dati esempio
    progress_data = {
        "Data": ["01/01", "02/01", "03/01", "04/01", "05/01"],
        "Testi Letti": [2, 3, 5, 4, 6],
        "Minuti di Studio": [30, 45, 60, 40, 75],
        "Parole Semplificate": [150, 200, 300, 250, 400]
    }
    
    df = pd.DataFrame(progress_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico linee
        fig1 = px.line(
            df, 
            x="Data", 
            y=["Testi Letti", "Parole Semplificate"],
            title="📈 Progressi Settimanali",
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Grafico a barre
        fig2 = px.bar(
            df,
            x="Data",
            y="Minuti di Studio",
            title="⏰ Tempo di Studio",
            color="Minuti di Studio",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Statistiche personali
    st.divider()
    st.markdown("### 🏆 Le tue Statistiche")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("🎯 Obiettivo Giornaliero", "45 min", "+15%")
    with col_stat2:
        st.metric("📖 Testi Completati", "12", "3 questa settimana")
    with col_stat3:
        st.metric("💪 Giorni di Fila", "5", "+2")

# TAB 6: Suggerimenti
with tab6:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💡 Suggerimenti Personalizzati")
        
        if openai_api_key:
            student_profile = st.text_area(
                "Descrivi le tue difficoltà o obiettivi:",
                placeholder="Es: Ho difficoltà a concentrarmi durante la lettura di testi lunghi...",
                height=100
            )
            
            if student_profile and st.button("🎯 Ottieni Suggerimenti", use_container_width=True):
                prompt = f"""
                Sono uno studente con queste caratteristiche:
                {student_profile}
                
                Dammi 5 suggerimenti pratici e personalizzati per:
                1. Migliorare la concentrazione
                2. Facilitare la lettura
                3. Organizzare lo studio
                4. Utilizzare strumenti compensativi
                5. Gestire il tempo
                """
                
                try:
                    with st.spinner("Generazione suggerimenti personalizzati..."):
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Sei un tutor esperto in DSA e metodi di studio inclusivi."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.8
                        )
                        
                        suggestions = response.choices[0].message.content
                        st.markdown(suggestions)
                        
                        # Salva i suggerimenti
                        if st.button("💾 Salva Suggerimenti"):
                            st.session_state.saved_texts.append({
                                'text': suggestions[:100] + "...",
                                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M"),
                                'type': 'suggerimenti'
                            })
                            st.success("Suggerimenti salvati!")
                            
                except Exception as e:
                    st.error(f"Errore: {str(e)}")
        else:
            st.info("🔑 Inserisci la tua OpenAI API Key nella sidebar per ottenere suggerimenti personalizzati")
    
    with col2:
        st.markdown("### 🎮 Esercizi Rapidi")
        
        st.markdown("""
        <div class="feature-card">
        <h4>👁️ Esercizio Visivo</h4>
        <p>Trova tutte le lettere 'A' nel testo in 30 secondi</p>
        </div>
        
        <div class="feature-card">
        <h4>🎧 Esercizio Uditivo</h4>
        <p>Ripeti dopo la sintesi vocale</p>
        </div>
        
        <div class="feature-card">
        <h4>🧩 Esercizio Logico</h4>
        <p>Ordina le frasi in sequenza logica</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>🧠 AI-DSA Assistant - Progetto Scolastico per l'Apprendimento Inclusivo</p>
    <p>⚠️ <strong>Importante:</strong> Questo è un prototipo educativo. Per uso reale, consultare sempre specialisti.</p>
</div>
""", unsafe_allow_html=True)

# Funzione per esportare dati
with st.sidebar:
    st.divider()
    if st.button("📤 Esporta Tutti i Dati"):
        export_data = {
            "saved_texts": st.session_state.saved_texts,
            "reading_time": st.session_state.reading_time,
            "statistics": {
                "total_texts": len(st.session_state.saved_texts),
                "total_minutes": st.session_state.reading_time
            }
        }
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Scarica JSON",
            data=json_str,
            file_name="dsa_assistant_data.json",
            mime="application/json"
        )
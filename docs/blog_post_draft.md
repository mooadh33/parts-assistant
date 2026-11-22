# Was ich beim Bau eines RAG-Assistenten für Kfz-Teiledaten gelernt habe (Entwurf)
_Ersetze die __-Stellen durch deine echten Zahlen und Erfahrungen. Schreibe nur, was du selbst erlebt hast._

**1. Warum das Projekt?** (2-3 Sätze: Aftermarket-Daten sind verstreut: PDFs, Kataloge, ERP.)
**2. Architektur in 5 Zeilen** (Chunking → Embeddings → Chroma → LLM mit Zitierpflicht; Router RAG/SQL).
**3. Drei Learnings**
- Chunking: Ich habe Fenster-Chunks mit Überschrift-Chunks verglichen: Ergebnis __ (Accuracy __% vs. __%).
- Sicherheit: Mein PII-Filter hat eine IBAN falsch behandelt, weil die Telefon-Regel zuerst lief. Tests vor Features.
- Modellwahl: Mein Benchmark mit __ Fragen zeigte: __ ist __% günstiger bei __ Qualitätsverlust.
**4. Was Nutzer überrascht hat** (aus dem Pilot, Zitate/Zahlen).
**5. Nächste Schritte** (Sprachassistent, Zeichnungsverständnis, Modell-Routing).

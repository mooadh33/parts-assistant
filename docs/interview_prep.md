# Interview-Vorbereitung: Fragen, die du beantworten können musst
1. **Warum diese Chunk-Größe / Strategie?** Ergebnis deines A/B-Vergleichs nennen (`ingest(strategy=...)`).
2. **Wie hast du Qualität gemessen?** Keyword-Treffer + LLM-Judge + Stichproben; Grenzen nennen (Keywords sind grob).
3. **Wie senkst du Kosten?** Cheap-Model fürs Routing, Modell-Wahl nach Benchmark, Kontext begrenzen (top-k), Rate Limits, Monitoring.
4. **Halluzinationen?** Zitierpflicht, „weiß nicht“-Regel, Kontext als Daten behandeln, unanswerable-Testfälle.
5. **Sicherheit?** JWT, Rate Limit, PII-Redaction, direkte + indirekte Injection, SQL read-only + Allow-List + Validator. Nenne den IBAN-Bug als Beispiel.
6. **Was würdest du für Produktion ändern?** Echter Embedder, Re-Ranking, Presidio, Redis-Limiter, SSO statt Passwörter, Audit-Log, Datenschutz/Betriebsrat, Evaluation auf echten Nutzerfragen.
7. **Wie hast du AI-Coding-Tools genutzt?** Konkret: was generiert, was selbst geprüft/getestet.
8. **Rollout?** Pilotgruppen, Feedback-Schleife, Schulung, Champions in Fachbereichen.

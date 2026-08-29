import re

class DictationPreprocessor:
    """Preprocesses raw speech-to-text dictation with deterministic rules for spoken punctuation and formatting commands."""

    @staticmethod
    def process(text: str) -> str:
        if not text:
            return ""

        cleaned = text

        # 1. Spoken Punctuation: Dos puntos
        cleaned = re.sub(r'(?i)\b(?:dos\s+puntos)\b', ':', cleaned)

        # 2. Spoken Punctuation: Punto y coma
        cleaned = re.sub(r'(?i)\b(?:punto\s+y\s+coma)\b', ';', cleaned)

        # 3. Spoken Punctuation: Punto y aparte / Nuevo párrafo
        cleaned = re.sub(r'(?i)\b(?:punto\s+y\s+aparte|nuevo\s+p[aá]rrafo)\b', '\n\n', cleaned)

        # 4. Spoken Punctuation: Punto y seguido / Punto final
        cleaned = re.sub(r'(?i)\b(?:punto\s+y\s+seguido)\b', '. ', cleaned)
        cleaned = re.sub(r'(?i)\b(?:punto\s+final)\b', '.', cleaned)

        # 5. Spoken Punctuation: Abro / Cierro paréntesis
        cleaned = re.sub(
            r'(?i)\b(?:abro|abrir)\s+par[eé]ntesis\s*(.*?)\s*(?:cierro|cerrar|cero)\s+par[eé]ntesis\b',
            r'(\1)',
            cleaned,
            flags=re.DOTALL
        )

        # 6. Spoken Punctuation: Entre paréntesis
        cleaned = re.sub(
            r'(?i)\bentre\s+par[eé]ntesis\s+([^,.;\n]+?)(?=[,.;\n]|$)',
            r'(\1)',
            cleaned
        )

        # 7. Common Whisper phonetic deformities of "entre paréntesis"
        cleaned = re.sub(
            r'(?i)\b(?:de\s+p[aá]nterismo|en\s+debarentesis|un\s+trepar[eé]ntesis|improbarentes|entreparece)\s+([^,.;\n]+?)(?=[,.;\n]|$)',
            r'(\1)',
            cleaned
        )

        # 8. Spoken Punctuation: Abro / Cierro comillas & Entre comillas
        cleaned = re.sub(
            r'(?i)\b(?:abro|abrir)\s+comillas\s*(.*?)\s*(?:cierro|cerrar|cero)\s+comillas\b',
            r'"\1"',
            cleaned,
            flags=re.DOTALL
        )
        cleaned = re.sub(
            r'(?i)\bentre\s+comillas\s+([^,.;\n]+?)(?=[,.;\n]|$)',
            r'"\1"',
            cleaned
        )

        # 9. Spoken Structure: Subpunto / Viñeta / Guión
        cleaned = re.sub(
            r'(?i)(?:^|\n)\s*(?:subpunto|gui[oó]n|vi[ñn]eta)\s*:?\s*',
            r'\n- ',
            cleaned
        )
        cleaned = re.sub(
            r'(?i)\b(?:subpunto|gui[oó]n|vi[ñn]eta)\s*:?\s*',
            r'\n- ',
            cleaned
        )

        # 10. Spoken Formatting: En negrita / Destacado
        cleaned = re.sub(
            r'(?i)\b(?:en\s+negrita|destacado)\s+([^,.;\n]+?)(?=[,.;\n]|$)',
            r'**\1**',
            cleaned
        )

        # 11. Normalize spaces around punctuation
        cleaned = re.sub(r'\s+:', ':', cleaned)
        cleaned = re.sub(r':(?!\s|\d)', ': ', cleaned)
        cleaned = re.sub(r'\(\s+', '(', cleaned)
        cleaned = re.sub(r'\s+\)', ')', cleaned)
        cleaned = re.sub(r'(?<=\w)\(', ' (', cleaned)
        cleaned = re.sub(r'\)(?=\w)', ') ', cleaned)
        cleaned = re.sub(r'(?<=\w)\s*"\s*(?=\w)', ' "', cleaned)
        cleaned = re.sub(r'(?<=\w)\s*"\s*(?=[,.;:\s]|$)', '"', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned.strip()

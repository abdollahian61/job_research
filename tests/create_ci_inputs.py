"""Synthetic CI inputs only. No real CV, account credentials or external calls."""
import json
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def main():
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica'),
                             NameObject('/Encoding'): NameObject('/WinAnsiEncoding')})
    page[NameObject('/Resources')] = DictionaryObject({
        NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 10 10 Td (Synthetic CI Kubernetes resume) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    targets = [Path('resume.pdf'), Path('.env'), Path('inputs/draft.json')]
    if any(path.exists() for path in targets):
        raise RuntimeError('CI fixture refuses to overwrite existing inputs.')
    writer.write(targets[0])
    targets[0].chmod(0o644)
    targets[1].write_text('SMTP_USERNAME=ci@example.com\nSEND_EMAILS=false\nTELEGRAM_ENABLED=false\n')
    targets[2].parent.mkdir(exist_ok=True)
    targets[2].write_text(json.dumps({'subject': 'CI dry run', 'body': 'Synthetic test only.'}))


if __name__ == '__main__':
    main()

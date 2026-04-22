from __future__ import annotations

from typing import Iterable


def _escape_pdf_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _normalize_lines(text: str) -> list[str]:
    raw_lines = []
    for block in str(text or "").replace("\r\n", "\n").split("\n"):
        block = block.strip()
        if not block:
            raw_lines.append("")
            continue
        while len(block) > 92:
            split_at = block.rfind(" ", 0, 92)
            if split_at <= 0:
                split_at = 92
            raw_lines.append(block[:split_at].strip())
            block = block[split_at:].strip()
        raw_lines.append(block)
    return raw_lines or [""]


def _build_stream(lines: Iterable[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    first = True
    for line in lines:
        escaped = _escape_pdf_text(line)
        if first:
            commands.append(f"({escaped}) Tj")
            first = False
        else:
            commands.append(f"T* ({escaped}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def render_text_pdf(*, title: str, text: str) -> bytes:
    lines = [title.strip(), ""] + _normalize_lines(text)
    pages = [lines[index:index + 45] for index in range(0, len(lines), 45)] or [["Documento"]]

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Count {len(pages)} /Kids [{kids}] >>".encode("ascii"))

    font_obj = 3 + len(pages) * 2
    for index, page_lines in enumerate(pages):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        stream = _build_stream(page_lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_obj} 0 R >>".encode(
                "ascii"
            )
        )
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("ascii")
    )
    return bytes(output)

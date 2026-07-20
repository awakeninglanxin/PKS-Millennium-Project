from pathlib import Path
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table

src = Path(r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\julia-set分形相关")
for name in ["Julia.docx", "fams-12-1826475.docx"]:
    p = src / name
    out = src / ("_" + name.replace(".docx", "") + "_extract.txt")
    doc = docx.Document(str(p))
    parts = []
    n_par = 0
    n_tab = 0
    for el in doc.element.body.iterchildren():
        if el.tag.endswith('}p'):
            para = Paragraph(el, doc)
            t = para.text
            if t.strip():
                parts.append(t)
                n_par += 1
        elif el.tag.endswith('}tbl'):
            tbl = Table(el, doc)
            n_tab += 1
            for row in tbl.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                parts.append(" | ".join(cells))
            parts.append("")
    txt = "\n".join(parts)
    out.write_text(txt, encoding="utf-8")
    print(f"{name}: {len(txt)} chars, {n_par} non-empty paras, {n_tab} tables -> {out.name}", flush=True)

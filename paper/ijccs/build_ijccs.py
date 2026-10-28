"""Build the IJCCS submission (.docx) from manuscript.md inside the official IJCCS English template.

The template's styles, headers/footers and page setup are kept; only the body is replaced. Paragraph formatting is
cloned from the template's own sample paragraphs (title, abstract, Heading1/2, body text, references), citations
[@key] are numbered in order of first appearance (IEEE, as the guidelines require) and the reference list is built
from REFS. Usage: python paper/ijccs/build_ijccs.py  ->  paper/ijccs/IJCCS_manuscript.docx
"""
import html
import pathlib
import re
import shutil
import tempfile
import zipfile

HERE = pathlib.Path(__file__).parent
TEMPLATE, SRC, OUT = HERE / "template_ijccs_en.docx", HERE / "manuscript.md", HERE / "IJCCS_manuscript.docx"
TEXT_WIDTH = 11906 - 2 * 1701  # A4 minus the template's 3 cm margins (twips)
TABLE_SZ = 18  # 9 pt in tables; body stays 11 pt as the template requires

REFS = {  # IEEE style with URL; all verified against OpenAlex/DOI (see paper/references.md)
    "kemenkes2022": 'Kementerian Kesehatan Republik Indonesia, "Peraturan Menteri Kesehatan Nomor 24 Tahun 2022 tentang Rekam Medis," Jakarta, 2022.',
    "kemenkes2023": 'Kementerian Kesehatan Republik Indonesia, "Kemenkes ajak fasyankes segera lakukan registrasi rekam medis elektronik," 2023. [Online]. Available: https://www.kemkes.go.id/id/kemenkes-ajak-fasyankes-segera-lakukan-registrasi-rekam-medis-elektronik',
    "hl7fhir": 'HL7 International, "FHIR Release 4 (v4.0.1)," 2019. [Online]. Available: https://hl7.org/fhir/R4/',
    "perpres39": 'Republik Indonesia, "Peraturan Presiden Nomor 39 Tahun 2019 tentang Satu Data Indonesia," 2019. [Online]. Available: https://peraturan.bpk.go.id/Details/108813',
    "cupid": 'J. Madhavan, P. A. Bernstein, and E. Rahm, "Generic schema matching with Cupid," in Proc. 27th Int. Conf. Very Large Data Bases (VLDB), 2001, pp. 49–58.',
    "coma": 'H.-H. Do and E. Rahm, "COMA — A system for flexible combination of schema matching approaches," in Proc. 28th Int. Conf. Very Large Data Bases (VLDB), 2002, pp. 610–621. [Online]. Available: https://doi.org/10.1016/B978-155860869-6/50060-3',
    "simflood": 'S. Melnik, H. Garcia-Molina, and E. Rahm, "Similarity flooding: A versatile graph matching algorithm and its application to schema matching," in Proc. 18th Int. Conf. Data Engineering (ICDE), 2002, pp. 117–128. [Online]. Available: https://doi.org/10.1109/ICDE.2002.994702',
    "valentine": 'C. Koutras, G. Siachamis, A. Ionescu, K. Psarakis, J. Brons, M. Fragkoulis, C. Lofi, A. Bonifati, and A. Katsifodimos, "Valentine: Evaluating matching techniques for dataset discovery," in Proc. IEEE 37th Int. Conf. Data Engineering (ICDE), 2021, pp. 468–479. [Online]. Available: https://doi.org/10.1109/ICDE51399.2021.00047',
    "smat": 'J. Zhang, B. Shin, J. D. Choi, and J. C. Ho, "SMAT: An attention-based deep learning solution to the automation of schema matching," in Advances in Databases and Information Systems (ADBIS), LNCS, 2021, pp. 260–274. [Online]. Available: https://doi.org/10.1007/978-3-030-82472-3_19',
    "unicorn": 'J. Tu, J. Fan, N. Tang, P. Wang, G. Li, X. Du, X. Jia, and S. Gao, "Unicorn: A unified multi-tasking model for supporting matching tasks in data integration," Proc. ACM Manag. Data, vol. 1, no. 1, 2023. [Online]. Available: https://doi.org/10.1145/3588938',
    "parciak": 'M. Parciak, B. Vandevoort, F. Neven, L. M. Peeters, and S. Vansummeren, "Schema matching with large language models: An experimental study," arXiv:2407.11852, 2024. [Online]. Available: https://doi.org/10.48550/arXiv.2407.11852',
    "rematch": 'E. Sheetrit, M. Brief, M. Mishaeli, and O. Elisha, "ReMatch: Retrieval enhanced schema matching with LLMs," arXiv:2403.01567, 2024. [Online]. Available: https://doi.org/10.48550/arXiv.2403.01567',
    "magneto": 'Y. Liu, E. H. M. Pena, A. S. R. Santos, E. Wu, and J. Freire, "Magneto: Combining small and large language models for schema matching," Proc. VLDB Endow., vol. 18, 2025. [Online]. Available: https://doi.org/10.14778/3742728.3742757',
    "matchmaker": 'N. Seedat and M. van der Schaar, "Matchmaker: Self-improving large language model programs for schema matching," arXiv:2410.24105, 2024. [Online]. Available: https://doi.org/10.48550/arXiv.2410.24105',
    "llmatch": 'S. Wang, Y. Li, H. Xiao, and B. T. Dai, "LLMATCH: A unified schema matching framework with large language models," in Lecture Notes in Computer Science, Springer, 2026. [Online]. Available: https://doi.org/10.1007/978-981-95-5722-6_37',
    "jellyfish": 'H. Zhang, Y. Dong, C. Xiao, and M. Oyamada, "Jellyfish: Instruction-tuning local large language models for data preprocessing," in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2024. [Online]. Available: https://doi.org/10.18653/v1/2024.emnlp-main.497',
    "gdcsm": 'A. Santos, E. Wu, R. Lopez, S. Keegan, et al., "GDC-SM: The GDC schema matching benchmark," arXiv:2412.08194, 2024. [Online]. Available: https://doi.org/10.48550/arXiv.2412.08194',
    "fhirgpt": 'Y. Li, H. Wang, H. Z. Yerebakan, Y. Shinagawa, and Y. Luo, "FHIR-GPT enhances health interoperability with large language models," NEJM AI, vol. 1, no. 8, 2024. [Online]. Available: https://doi.org/10.1056/AIcs2300301',
    "nameguess": 'J. Zhang, Z. Shen, B. Srinivasan, S. Wang, H. Rangwala, and G. Karypis, "NameGuess: Column name expansion for tabular data," in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2023. [Online]. Available: https://doi.org/10.18653/v1/2023.emnlp-main.820',
    "columbo": 'T. Cai, S. Sheen, and A. Doan, "Columbo: Expanding abbreviated column names for tabular data using large language models," in Findings of the Assoc. for Computational Linguistics: EMNLP, 2025. [Online]. Available: https://doi.org/10.18653/v1/2025.findings-emnlp.1348',
    "indonlg": 'S. Cahyawijaya, G. I. Winata, B. Wilie, K. Vincentio, et al., "IndoNLG: Benchmark and resources for evaluating Indonesian natural language generation," in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2021. [Online]. Available: https://doi.org/10.18653/v1/2021.emnlp-main.699',
    "nusax": 'G. I. Winata, A. F. Aji, S. Cahyawijaya, R. Mahendra, et al., "NusaX: Multilingual parallel sentiment dataset for 10 Indonesian local languages," in Proc. 17th Conf. European Chapter of the Assoc. for Computational Linguistics (EACL), 2023. [Online]. Available: https://doi.org/10.18653/v1/2023.eacl-main.57',
    "prereg": 'E. van Miltenburg, C. van der Lee, and E. Krahmer, "Preregistering NLP research," in Proc. Conf. North American Chapter of the Assoc. for Computational Linguistics (NAACL-HLT), 2021. [Online]. Available: https://doi.org/10.18653/v1/2021.naacl-main.51',
    "bgem3": 'J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, and Z. Liu, "M3-Embedding: Multi-linguality, multi-functionality, multi-granularity text embeddings through self-knowledge distillation," in Findings of the Assoc. for Computational Linguistics: ACL, 2024. [Online]. Available: https://doi.org/10.18653/v1/2024.findings-acl.137',
    "qwen3": 'A. Yang et al., "Qwen3 technical report," arXiv:2505.09388, 2025. [Online]. Available: https://doi.org/10.48550/arXiv.2505.09388',
    "glm": 'Z.ai, "GLM-5.3-Flash," model card, 2026. [Online]. Available: https://huggingface.co/zai-org/GLM-5.3-Flash',
    "lostmiddle": 'N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, "Lost in the middle: How language models use long contexts," Trans. Assoc. Comput. Linguist., vol. 12, pp. 157–173, 2024. [Online]. Available: https://doi.org/10.1162/tacl_a_00638',
    "negated": 'J. Jang, S. Ye, and M. Seo, "Can large language models truly understand prompts? A case study with negated prompts," arXiv:2209.12711, 2022. [Online]. Available: https://doi.org/10.48550/arXiv.2209.12711',
    "contamination": 'O. Sainz, J. A. Campos, I. García-Ferrero, J. Etxaniz, O. Lopez de Lacalle, and E. Agirre, "NLP evaluation in trouble: On the need to measure LLM data contamination for each benchmark," in Findings of the Assoc. for Computational Linguistics: EMNLP, 2023. [Online]. Available: https://doi.org/10.18653/v1/2023.findings-emnlp.722',
}


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def runs(text: str, rpr: str) -> str:
    """Inline markup -> w:r runs: *italic*, ^superscript^, `code` (plain), with the template paragraph's rPr."""
    out = []
    for tok in re.split(r"(\*[^*]+\*|\^[^^]+\^|`[^`]+`)", text):
        if not tok:
            continue
        extra, t = "", tok
        if tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            extra, t = "<w:i/>", tok[1:-1]
        elif tok.startswith("^") and tok.endswith("^"):
            extra, t = '<w:vertAlign w:val="superscript"/>', tok[1:-1]
        elif tok.startswith("`"):
            t = tok[1:-1]
        r = rpr.replace("</w:rPr>", extra + "</w:rPr>") if extra else rpr
        out.append(f'<w:r>{r}<w:t xml:space="preserve">{esc(t)}</w:t></w:r>')
    return "".join(out)


class Template:
    """Sample paragraphs of the IJCCS template, found by their text, used as formatting prototypes."""

    def __init__(self, xml: str):
        self.paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)

    def proto(self, needle: str) -> tuple[str, str]:
        p = next(p for p in self.paras if needle in "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
        ppr = (re.search(r"<w:pPr>.*?</w:pPr>", p, re.S) or [""])[0]
        rs = re.findall(r"<w:r>(<w:rPr>.*?</w:rPr>)(.*?)</w:r>", p, re.S)
        rpr = max(rs, key=lambda r: len("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", r[1]))))[0] if rs else "<w:rPr></w:rPr>"
        rpr = re.sub(r'<w:vertAlign[^>]*/>', "", rpr)
        return ppr, re.sub(r"<w:b/>|<w:b [^>]*/>|<w:i/>|<w:i [^>]*/>|<w:caps[^>]*/>", "", rpr)


def keep_next(ppr: str) -> str:
    ppr = re.sub(r"<w:spacing [^>]*/>", "", ppr)
    return ppr.replace("<w:pPr>", '<w:pPr><w:keepNext/><w:spacing w:before="160" w:after="40"/>', 1)


def para(ppr: str, rpr: str, text: str, bold=False, italic=False, center=False, not_bold=False) -> str:
    extra = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + ('<w:b w:val="false"/><w:bCs w:val="false"/>' if not_bold else "")
    r = rpr.replace("<w:rPr>", "<w:rPr>" + extra, 1) if extra else rpr
    if center:
        ppr = re.sub(r'<w:jc w:val="[^"]+"/>', "", ppr).replace("</w:pPr>", '<w:jc w:val="center"/></w:pPr>', 1)
    return f"<w:p>{ppr}{runs(text, r)}</w:p>"


def table(rows: list[list[str]]) -> str:
    ncol = max(map(len, rows))
    # ponytail: char-count width heuristic (~100 twips per char at 9 pt); every column fits its longest word, the
    # rest of the text width goes to columns with long cells. Ceiling: proportional fonts, so very wide words may wrap.
    cells = [[(r[i] if i < len(r) else "").replace("`", "") for r in rows] for i in range(ncol)]
    min_w = [max(len(w) for c in col for w in (c.split() or [""])) * 100 + 220 for col in cells]
    extra = [max(max(map(len, col)) * 100 + 220 - m, 0) for col, m in zip(cells, min_w)]
    spare = max(TEXT_WIDTH - sum(min_w), 0)
    widths = [m + (spare * e // sum(extra) if sum(extra) else spare // ncol) for m, e in zip(min_w, extra)]
    widths = [w * TEXT_WIDTH // sum(widths) for w in widths]
    widths[-1] += TEXT_WIDTH - sum(widths)
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
                     for s in ("top", "start", "bottom", "end"))
    rpr = f'<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="{TABLE_SZ}"/><w:szCs w:val="{TABLE_SZ}"/></w:rPr>'
    trs = []
    for ri, r in enumerate(rows):
        tcs = []
        for i, w in enumerate(widths):
            cell = r[i] if i < len(r) else ""
            jc = "left" if i == 0 else "center"
            tcs.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:tcBorders>{border}</w:tcBorders></w:tcPr>'
                       f'<w:p><w:pPr>{"<w:keepNext/>" if ri < len(rows) - 1 else ""}<w:spacing w:before="0" w:after="0"/><w:jc w:val="{jc}"/></w:pPr>{runs(cell, rpr)}</w:p></w:tc>')
        trs.append(f"<w:tr><w:trPr><w:cantSplit/>{'<w:tblHeader/>' if ri == 0 else ''}</w:trPr>{''.join(tcs)}</w:tr>")
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
            f'<w:tblCellMar><w:start w:w="80" w:type="dxa"/><w:end w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f"<w:tblGrid>{grid}</w:tblGrid>{''.join(trs)}</w:tbl>")


FIGS: list[pathlib.Path] = []


def image(path: pathlib.Path) -> str:
    """Inline picture spanning the text width; the file is added to word/media in main()."""
    FIGS.append(path)
    n = len(FIGS)
    w, h = (int(x) for x in re.findall(r"pixel(?:Width|Height): (\d+)", __import__("subprocess").run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], capture_output=True, text=True).stdout))
    cx = TEXT_WIDTH * 635
    cy = cx * h // w
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{100 + n}" name="Figure {n}"/>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{100 + n}" name="fig{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="rIdFig{n}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def cite(text: str, order: list[str]) -> str:
    def repl(m):
        keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
        for k in keys:
            assert k in REFS, f"unknown citation {k}"
            if k not in order:
                order.append(k)
        return "[" + ",".join(str(order.index(k) + 1) for k in keys) + "]"
    return re.sub(r"\[(@[^\]]+)\]", repl, text)


def body(tpl: Template, src: str) -> str:
    title_p = tpl.proto("Title of Maximum Publication")
    author_p, affil_p, email_p = tpl.proto("First Author"), tpl.proto("Institution/affiliation"), tpl.proto("e-mail:")
    abs_head, abs_text = tpl.proto("Abstrak"), tpl.proto("Abstrak maksimal")
    kw = tpl.proto("Kata kunci")
    en_text = tpl.proto("Abstract is written")
    h1, h2 = tpl.proto("INTRODUCTION"), tpl.proto("Stage Review")
    txt_first, txt = tpl.proto("This document is a template"), tpl.proto("The paper is written with Times")
    ref_p = tpl.proto("Zulfikar")
    cap_p = tpl.proto("Citra lena")
    meta = dict(re.findall(r"^%(\w+) (.+)$", src, re.M))
    blocks = dict(re.findall(r"^%(abstrak|abstract)\n(.+?)\n%", src, re.M | re.S))
    out = [para(*title_p, meta["title"], center=True, not_bold=True), para(*author_p, meta["authors"], bold=True, center=True),
           para(*affil_p, meta["affil"], center=True), para(*email_p, meta["email"], center=True)]
    for head, key, kwkey, label in (("Abstrak", "abstrak", "katakunci", "Kata kunci"),
                                    ("Abstract", "abstract", "keywords", "Keywords")):
        out += [para(*abs_head, head, bold=True, italic=True, center=True),
                para(*(abs_text if key == "abstrak" else en_text), blocks[key].strip(), italic=True),
                para(*kw, f"{label}—{meta[kwkey]}", bold=True, italic=True)]
    order, first, lines, i = [], True, src.split("\n"), 0
    lines = lines[next(n for n, l in enumerate(lines) if l.startswith("# ")):]
    while i < len(lines):
        line = cite(lines[i].rstrip(), order)
        if line.startswith("# "):
            out.append(para(*h1, line[2:]))
            first = True
        elif line.startswith("## "):
            out.append(para(*h2, line[3:]))
            first = True
        elif line.startswith("!["):
            out.append(image(HERE / re.search(r"\((.+?)\)", line).group(1)))
            i += 1
            out.append(para(*cap_p, cite(lines[i], order), center=True))
            first = True
        elif line.startswith("Table ") and i + 1 < len(lines) and lines[i + 1].startswith("|"):
            out.append(para(keep_next(cap_p[0]), cap_p[1], line, center=True))
            rows = []
            while i + 1 < len(lines) and lines[i + 1].startswith("|"):
                i += 1
                row = cite(lines[i], order).strip()
                # cells are separated by " | " so that "R@|GT|" inside a cell stays intact
                rows.append([c.strip() for c in row.removeprefix("|").removesuffix("|").strip().split(" | ")])
            out.append(table(rows))
            out.append(para(*txt_first, ""))
            first = True
        elif line.strip():
            out.append(para(*(txt_first if first else txt), line))
            first = False
        i += 1
    out.append(para(*h1, "REFERENCES"))
    out += [f"<w:p>{ref_p[0]}{runs(f'[{n}]', ref_p[1])}<w:r><w:tab/></w:r>{runs(REFS[k], ref_p[1])}</w:p>"
            for n, k in enumerate(order, 1)]
    unused = set(REFS) - set(order)
    assert not unused, f"references never cited: {unused}"
    print(f"{len(order)} references, cited in order of first appearance")
    return "".join(out)


def main():
    src = SRC.read_text()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        with zipfile.ZipFile(TEMPLATE) as z:
            z.extractall(tmp)
        doc = (tmp / "word/document.xml").read_text(encoding="utf8")
        sect = re.findall(r"<w:sectPr.*?</w:sectPr>", doc, re.S)[-1]
        head, tail = doc[: doc.index("<w:body>") + len("<w:body>")], "</w:body>" + doc.split("</w:body>", 1)[1]
        (tmp / "word/document.xml").write_text(head + body(Template(doc), src) + sect + tail, encoding="utf8")
        rels = tmp / "word/_rels/document.xml.rels"
        r = rels.read_text(encoding="utf8")
        for n, f in enumerate(FIGS, 1):
            shutil.copy(f, tmp / f"word/media/fig{n}.png")
            r = r.replace("</Relationships>", f'<Relationship Id="rIdFig{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/fig{n}.png"/></Relationships>')
        rels.write_text(r, encoding="utf8")
        ct = tmp / "[Content_Types].xml"
        c = ct.read_text(encoding="utf8")
        if 'Extension="png"' not in c:
            ct.write_text(c.replace("<Types ", '<Types ', 1).replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>'), encoding="utf8")
        title = re.search(r"^%title (.+)$", src, re.M).group(1)
        for f in (tmp / "word").glob("footer*.xml"):
            x = f.read_text(encoding="utf8")
            x = x.replace("Title of manuscript is short and clear, implies research results", esc(title))
            f.write_text(x, encoding="utf8")
        OUT.unlink(missing_ok=True)
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(tmp.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(tmp).as_posix())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

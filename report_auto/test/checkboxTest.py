from docx import Document
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn


def add_checkbox(doc):
    # 创建一个段落
    p = doc.add_paragraph()

    # 定义命名空间
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

    # 创建内容控件的XML结构
    fldChar = OxmlElement('w:fldChar')  # 开始字段字符
    fldChar.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'CHECKBOX "\\b"'

    fldChar2 = OxmlElement('w:fldChar')  # 结束字段字符
    fldChar2.set(qn('w:fldCharType'), 'end')

    # 将这些元素添加到段落中
    p._p.append(fldChar)
    p._p.append(instrText)
    p._p.append(fldChar2)

    return doc


# 创建一个新的Word文档
doc = Document()

# 添加复选框
add_checkbox(doc)

# 保存文档
doc.save('checkbox_content_control.docx')
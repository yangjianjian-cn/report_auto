from docx import Document
from docxcompose.composer import Composer


def merge_docs(output_path, *input_paths):
    # 初始化第一个文档
    master = Document(input_paths[0])
    composer = Composer(master)

    # 合并后续文档
    for input_path in input_paths[1:]:
        doc = Document(input_path)
        composer.append(doc)

    # 保存合并后的文档
    composer.save(output_path)


# 定义需要合并的文件路径
file_paths = [
    r'C:\Users\Administrator\Downloads\output\MST_Test\docx\APP_PL_BR_1.docx',
    r'C:\Users\Administrator\Downloads\output\MST_Test\docx\Clth_05.docx',
    r'C:\Users\Administrator\Downloads\output\MST_Test\docx\Clth_06.docx'
]

# 指定输出文件的路径
output_file_path = r'C:\Users\Administrator\Downloads\output\MST_Test\docx\merged_document.docx'

# 调用函数进行合并
merge_docs(output_file_path, *file_paths)

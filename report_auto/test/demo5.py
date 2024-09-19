msg = ['succeed:C:\\Users\\Administrator\\Downloads\\output\\MST_Test\\docx\\Brk_04.docx']
contains_succeed = any('succeed' in m for m in msg)
print(contains_succeed)
new_msg = [m.replace('succeed:', '') for m in msg]
print(new_msg)


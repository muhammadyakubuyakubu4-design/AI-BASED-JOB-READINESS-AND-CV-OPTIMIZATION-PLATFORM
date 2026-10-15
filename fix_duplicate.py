import re
with open('templates/resume_templates/elegant.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'<td class="sidebar".*?>', '<td class="sidebar" style="vertical-align: top; width: 35%; padding: 0; margin: 0; background-color: #eaedf1;">', text)
text = re.sub(r'<td class="main-content".*?>', '<td class="main-content" style="vertical-align: top; width: 65%; padding: 0; margin: 0; border: none;">', text)

with open('templates/resume_templates/elegant.html', 'w', encoding='utf-8') as f:
    f.write(text)

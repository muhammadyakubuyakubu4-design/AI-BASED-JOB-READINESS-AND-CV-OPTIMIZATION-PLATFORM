import re

with open('templates/resume_templates/elegant.html', 'r', encoding='utf-8') as f:
    text = f.read()

# CSS Fixes
text = text.replace('display: flex;', '')
text = text.replace('flex-direction: column;', '')
text = text.replace('align-items: center;', 'text-align: center;')
text = text.replace('justify-content: center;', '')
text = text.replace('flex-grow: 1;', '')

# HTML Structure Fixes
text = text.replace('<div class="resume-page">', '<table class="resume-page" style="width: 100%; margin: 0; padding: 0; border-collapse: collapse; table-layout: fixed; background: #fff;"><tr>')
text = text.replace('<div class="sidebar">', '<td class="sidebar" style="vertical-align: top; width: 35%; background-color: #eaedf1;">')
text = text.replace('<div class="main-content">', '</td>\n<td class="main-content" style="vertical-align: top; width: 65%; padding: 0;">')
# Close table at the end (replacing the last closing divs)
parts = text.rsplit('</div>', 2)
if len(parts) == 3:
    text = '</td></tr></table>'.join([parts[0], parts[1], parts[2]])

with open('templates/resume_templates/elegant.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done fixing layout!")

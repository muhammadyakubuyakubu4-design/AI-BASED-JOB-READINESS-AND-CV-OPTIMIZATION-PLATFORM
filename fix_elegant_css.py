import re

css = """<style>
  @page { margin: 0; size: letter; }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { 
    font-family: 'Montserrat', sans-serif; 
    font-size: 10pt; 
    line-height: 1.5; 
    color: #333; 
    background: #fff;
    margin: 0;
    padding: 0;
  }
  
  .resume-page { 
    width: 8.5in; 
    min-height: 11in; 
    background: #fff; 
  }
  
  /* Left Sidebar */
  .sidebar {
    width: 35%;
    background-color: #eaedf1;
    text-align: left;
  }
  
  .profile-pic-container {
    width: 100%;
    height: 1.5in;
    background-color: #eaedf1;
    text-align: center;
    margin-bottom: 20px;
    margin-top: 30px;
  }
  
  .profile-pic {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    border: 6px solid #fff;
  }
  
  .sidebar-section {
    width: 100%;
    padding: 0 30px;
    margin-bottom: 25px;
  }
  
  .sidebar-title {
    font-size: 13pt;
    font-weight: 800;
    color: #243b55;
    letter-spacing: 2px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #a3b0bd;
    text-transform: uppercase;
    text-align: center;
  }
  
  .contact-item {
    margin-bottom: 12px;
    font-size: 9.5pt;
    color: #4a5568;
    word-break: break-all;
  }
  
  .contact-item i {
    width: 20px;
    color: #243b55;
    margin-top: 3px;
    text-align: center;
  }
  
  .skill-list {
    list-style-type: none;
    color: #4a5568;
    padding-left: 0;
    margin: 0;
  }
  
  .skill-list li {
    margin-bottom: 8px;
    font-size: 9.5pt;
    position: relative;
    padding-left: 15px;
  }
  
  .skill-list li::before {
    content: '-';
    position: absolute;
    left: 0;
    color: #243b55;
    font-weight: bold;
  }
  
  /* Right Content */
  .main-content {
    width: 65%;
  }
  
  .header {
    background-color: #243b55;
    color: #fff;
    height: 1.7in;
    padding: 30px 40px;
  }
  
  .name {
    font-size: 26pt;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    margin-top: 20px;
  }
  
  .job-title {
    font-size: 10.5pt;
    font-weight: 400;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #cbd5e1;
  }
  
  .content-body {
    padding: 30px 40px;
  }
  
  .section {
    margin-bottom: 25px;
  }
  
  .section-title {
    font-size: 15pt;
    font-weight: 800;
    color: #243b55;
    letter-spacing: 1px;
    margin-bottom: 15px;
    text-transform: uppercase;
    border-bottom: 2px solid #243b55;
    padding-bottom: 8px;
    text-align: left;
  }
  
  .section-icon {
    display: inline-block;
    width: 32px;
    height: 32px;
    background-color: #243b55;
    color: #fff;
    border-radius: 50%;
    margin-right: 15px;
    font-size: 12pt;
    text-align: center;
    line-height: 32px;
  }
  
  .item {
    margin-bottom: 18px;
  }
  
  .item-title {
    font-size: 12pt;
    font-weight: 700;
    color: #243b55;
  }
  
  .item-subtitle {
    font-size: 10.5pt;
    font-weight: 600;
    color: #4a5568;
  }
  
  .item-date {
    font-size: 9pt;
    font-weight: 700;
    margin: 4px 0 8px 0;
    text-transform: uppercase;
    color: #1e293b;
  }
  
  .item-desc {
    color: #334155;
    font-size: 9.5pt;
  }
  
  .profile-text {
    color: #334155;
    font-size: 10pt;
  }
</style>"""

with open('templates/resume_templates/elegant.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the style block
html = re.sub(r'<style>.*?</style>', css, html, flags=re.DOTALL)

# Ensure the table layout is flawless
html = re.sub(r'<table.*?>', '<table class="resume-page" style="width: 100%; height: 100%; border: none; margin: 0; padding: 0; border-collapse: collapse; border-spacing: 0; background: #fff;">', html)
html = html.replace('<td class="sidebar"', '<td class="sidebar" style="vertical-align: top; width: 35%; padding: 0; margin: 0; background-color: #eaedf1;"')
html = html.replace('<td class="main-content"', '<td class="main-content" style="vertical-align: top; width: 65%; padding: 0; margin: 0; border: none;"')

with open('templates/resume_templates/elegant.html', 'w', encoding='utf-8') as f:
    f.write(html)

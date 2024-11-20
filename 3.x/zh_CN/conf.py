# -*- coding: utf-8 -*-
import sys
import os
import jieba
from pathlib import Path
import sphinx_rtd_theme

# 项目目录配置
DOC_SOURCES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(DOC_SOURCES_DIR))
sys.path.insert(0, DOC_SOURCES_DIR)
print('PROJECT_ROOT_DIR', PROJECT_ROOT_DIR)

# 检测是否在 ReadTheDocs 环境中运行
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# Markdown 支持的文件后缀
source_suffix = ['.rst', '.md']

# 项目信息
project = u'FISCO BCOS 3.0'
copyright = u'© 2022. All rights reserved.'
author = u'fisco-bcos-dev'

# 项目版本信息
version = '3.0'
release = 'v3.11.0'

# 语言支持
language = 'zh_CN'

# 搜索配置（确保中文索引功能正常）
html_search_language = 'zh'
current_dir = Path(__file__).parent.resolve()
package_path = [p for p in sys.path if 'site-packages' in p][0]  # 找到 jieba 的安装路径
dict_path = Path(package_path) / 'jieba/dict.txt'  # jieba 默认词典路径

custom_dict_path = current_dir / "custom_words.txt"  # 自定义词典路径
if custom_dict_path.exists():
    custom_words = custom_dict_path.read_text(encoding="utf-8").splitlines()
    custom_words = [f"{word} 3 n" for word in custom_words if word.strip()]
    dict_texts = dict_path.read_text(encoding="utf-8").splitlines()
    dict_texts.extend(custom_words)
    dict_path.write_text("\n".join(dict_texts), encoding="utf-8")

html_search_options = {
    'dict': str(dict_path),
    'split_all': True,  # 开启全分词模式
    'minchars': 2,      # 最小搜索字符数
    'maxchars': 10,    # 最大搜索字符数
}

# Sphinx 扩展
extensions = [
    'sphinx_copybutton',
    'sphinxcontrib.mermaid',
    'sphinx.ext.mathjax',
    'sphinx_markdown_tables',
    'myst_parser',  # 使用 myst-parser 支持 Markdown
]

# Markdown 配置
myst_enable_extensions = [
    "linkify",         # 自动转换 URL 为链接
    "replacements",    # 支持文本替换
    "smartquotes",     # 美化引号
    "strikethrough",   # 支持删除线
    "substitution",    # 支持替换变量
    "attrs_block",     # 支持 Markdown 块级属性
]

# 模板和静态文件路径
templates_path = ['../_templates']
html_static_path = ['../_static']

# 主文档
master_doc = 'index'

# HTML 输出选项
html_theme = 'sphinx_rtd_theme'
html_theme_options = {'navigation_depth': 3}
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_context = {
    "display_github": True,
    "github_repo": "FISCO-BCOS-DOC",
    "github_user": "FISCO-BCOS",
    "github_version": "release-3",
    "conf_py_path": "/3.x/zh_CN/",
}
html_extra_path = ['../_static', '../../2.x/images', 'images', './docs/sdk/java_sdk/javadoc']
html_show_sourcelink = True
html_use_index = True

# 搜索引擎索引支持
pygments_style = 'sphinx'

# LaTeX 配置
latex_engine = 'pdflatex'
latex_use_xindy = False
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    'preamble': r'''
\hypersetup{unicode=true}
\usepackage{CJKutf8}
\DeclareUnicodeCharacter{00A0}{\nobreakspace}
\DeclareUnicodeCharacter{2203}{\ensuremath{\exists}}
\DeclareUnicodeCharacter{2200}{\ensuremath{\forall}}
\DeclareUnicodeCharacter{2286}{\ensuremath{\subseteq}}
\DeclareUnicodeCharacter{2713}{x}
\DeclareUnicodeCharacter{01F5}{x}
\DeclareUnicodeCharacter{27FA}{\ensuremath{\Longleftrightarrow}}
\DeclareUnicodeCharacter{221A}{\ensuremath{\sqrt{}}}
\DeclareUnicodeCharacter{221B}{\ensuremath{\sqrt[3]{}}}
\DeclareUnicodeCharacter{2295}{\ensuremath{\oplus}}
\DeclareUnicodeCharacter{2297}{\ensuremath{\otimes}}
\begin{CJK}{UTF8}{gbsn}
\AtEndDocument{\end{CJK}}
''',
}

latex_documents = [
    (master_doc, 'FISCO-BCOS.tex', u'FISCO BCOS Documentation',
     u'fisco-dev', 'manual'),
]

man_pages = [
    (master_doc, 'FISCO BCOS', u'FISCO BCOS Documentation',
     [author], 1)
]

texinfo_documents = [
    (master_doc, 'FISCO BCOS', u'FISCO BCOS Documentation',
     author, 'fisco-dev', 'documents of FISCO BCOS',
     'Miscellaneous'),
]

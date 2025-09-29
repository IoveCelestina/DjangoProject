import os, re, subprocess, sys, json, pathlib, shutil
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
COL = DOCS / '_collected'
COL.mkdir(parents=True, exist_ok=True)

EXCLUDES = re.compile(r"node_modules|dist|build|\\.git|venv|__pycache__|\\.idea|\\.vscode|migrations|\\.pytest_cache")


def run(cmd, cwd=ROOT, to_file=None):
    try:
        out = subprocess.check_output(cmd, cwd=cwd, shell=True, stderr=subprocess.STDOUT)
        text = out.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        text = e.output.decode('utf-8', errors='ignore')
    if to_file:
        (COL / to_file).write_text(text, encoding='utf-8')
    return text


def write(name, content):
    (COL / name).write_text(content, encoding='utf-8')


# 1) 目录树（尽力调用系统 tree，失败则自建）
if shutil.which('tree'):
    run("tree -I 'node_modules|dist|build|.git|venv|__pycache__|.idea|.vscode|migrations|.pytest_cache' -L 6", to_file='repo_tree.txt')
else:
    lines = []
    for p, ds, fs in os.walk(ROOT):
        rel = os.path.relpath(p, ROOT)
        if EXCLUDES.search(rel.replace('\\\\','/')):
            ds[:] = []
            continue
        depth = 0 if rel == '.' else rel.count(os.sep)
        indent = '  ' * depth
        lines.append(f"{indent}{os.path.basename(p) if rel!='.' else '.'}")
        for f in fs:
            if EXCLUDES.search(f):
                continue
            lines.append(f"{indent}  {f}")
    write('repo_tree.txt', '\n'.join(lines))

# 2) Python 依赖
if shutil.which(sys.executable):
    run(f"{sys.executable} -m pip freeze", to_file='deps-python.txt')
    if shutil.which('pipdeptree'):
        run("pipdeptree --warn silence", to_file='deps-python-tree.txt')

# 3) Node 依赖（如存在 package.json）
if (ROOT / 'package.json').exists() or (ROOT / 'frontend' / 'package.json').exists():
    FE = ROOT if (ROOT / 'package.json').exists() else (ROOT / 'frontend')
    if shutil.which('node') and shutil.which('npm'):
        run("node -v", cwd=FE, to_file='node-version.txt')
        run("npm -v", cwd=FE, to_file='npm-version.txt')
        run("npm ls --depth=0", cwd=FE, to_file='deps-node.txt')

# 4) Django 路由（show_urls 优先）
manage_py = None
for cand in ROOT.rglob('manage.py'):
    manage_py = cand
    break

if manage_py:
    env = os.environ.copy()
    # 尝试 show_urls
    out = run(f"{sys.executable} {manage_py} show_urls --format=aligned", cwd=manage_py.parent)
    if 'Unknown command' not in out and out.strip():
        write('django-urls.txt', out)
    else:
        # 兜底：直接搜 path/re_path
        agg = []
        for f in ROOT.rglob('urls.py'):
            try:
                text = f.read_text(encoding='utf-8', errors='ignore')
                for m in re.finditer(r"(path|re_path)\((.+?)\)", text, re.S):
                    agg.append(f"{f}: {m.group(0).strip()}")
            except Exception:
                pass
        write('django-urls-grep.txt', '\n'.join(agg))

# 5) Vue 路由（粗略提取）
agg = []
for f in ROOT.rglob('src/router/*.js'):
    try:
        text = f.read_text(encoding='utf-8', errors='ignore')
        for line in text.splitlines():
            if 'path:' in line or 'name:' in line or 'component:' in line or 'meta:' in line:
                agg.append(f"{f.name}: {line.strip()}")
    except Exception:
        pass
for f in ROOT.rglob('src/router/*.ts'):
    try:
        text = f.read_text(encoding='utf-8', errors='ignore')
        for line in text.splitlines():
            if 'path:' in line or 'name:' in line or 'component:' in line or 'meta:' in line:
                agg.append(f"{f.name}: {line.strip()}")
    except Exception:
        pass
if agg:
    write('vue-routes.txt', '\n'.join(agg))

# 6) 生成草稿文档
now = datetime.now().strftime('%Y-%m-%d %H:%M')
draft = f"""
# 项目技术文档（草稿）

> 生成时间：{now}

## 1. 概览
- 技术栈：Django + Vue3 + Element-Plus + MySQL（具体以 deps-* 为准）
- 目录：详见 `docs/_collected/repo_tree.txt`

## 2. 部署
- Python 依赖：见 `docs/_collected/deps-python.txt`
- Node 依赖：见 `docs/_collected/deps-node.txt`

## 3. 路由与接口（后端）
- Django 路由：`docs/_collected/django-urls.txt`（或 `django-urls-grep.txt`）

## 4. 前端路由
- Vue Router：`docs/_collected/vue-routes.txt`

## 5. 数据库
- 如提供 `schema.sql` 或 `models_from_db.py`，将在正式文档中展开 ER 与字段字典。

## 6. 任务与外部集成
- 待根据你提供的计划任务脚本与第三方调用代码完善。

## 7. 常见问题
- CORS / JWT / 依赖冲突 / Windows 计划任务权限 等。
"""
(DOCS / 'DOCS_DRAFT.md').write_text(draft, encoding='utf-8')

print("[OK] 已输出到:")
print(f" - {COL}")
print(f" - {DOCS / 'DOCS_DRAFT.md'}")

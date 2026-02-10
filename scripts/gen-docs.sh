#!/bin/bash
# 一键生成 MkDocs 站点和 pdoc 本地 API 参考
set -e

# MkDocs
echo "==> 构建 MkDocs 文档..."
mkdocs build -d site/

# pdoc
echo "==> 构建 pdoc API 参考..."
pdoc --html --output-dir site/pdoc src/qmt_bridge/client/

echo "==> 完成！"
echo "    MkDocs: site/index.html"
echo "    pdoc:   site/pdoc/qmt_bridge/client/index.html"

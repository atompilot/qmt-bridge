#!/bin/bash
# 顺序发送 4 个请求，测试是否仍然崩溃
BASE="http://localhost:18888"

echo "=== 顺序测试：逐个发送请求 ==="
echo ""

echo "1/4: 沪深A股..."
curl -s --max-time 10 "$BASE/api/sector_stocks?sector=%E6%B2%AA%E6%B7%B1A%E8%82%A1" | head -c 100
echo ""
echo "--- 完成 ---"
sleep 0.5

echo "2/4: ETF列表..."
curl -s --max-time 10 "$BASE/api/etf/list" | head -c 100
echo ""
echo "--- 完成 ---"
sleep 0.5

echo "3/4: 上证指数..."
curl -s --max-time 10 "$BASE/api/sector_stocks?sector=%E4%B8%8A%E8%AF%81%E6%8C%87%E6%95%B0" | head -c 100
echo ""
echo "--- 完成 ---"
sleep 0.5

echo "4/4: 深证指数..."
curl -s --max-time 10 "$BASE/api/sector_stocks?sector=%E6%B7%B1%E8%AF%81%E6%8C%87%E6%95%B0" | head -c 100
echo ""
echo "--- 完成 ---"

echo ""
echo "=== 顺序测试完成 ==="

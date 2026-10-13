# Tổng quan và bàn giao bài lab

Dự án là pipeline Python GPU FinOps cho NimbusAI: dữ liệu tổng hợp → kiểm toán hiệu quả (M1) → tối ưu inference (M2) → purchasing (M3) → allocation (M4) → báo cáo và waterfall (M5).
Đã đọc README, Guide, CODELAB, Rubric, các module finops, missions và bộ tests gốc.

## Các yêu cầu đã hoàn thành

- Sinh lại dữ liệu seed=25; chạy M1–M5.
- Báo cáo baseline/optimized, % savings, bốn lever, $/1M-token, sustainability và hành động ưu tiên: [report.md](report.md).
- Biểu đồ waterfall đã kiểm tra hiển thị: [savings.png](savings.png).
- FOCUS-style sample 50 request: [focus_export.csv](focus_export.csv).
- Hai extension có code và số liệu: reasoning budget (cap 10% và sensitivity 5%), carbon-aware scheduling (tất cả 5 vùng và từng job interruptible).
- Bài viết ngắn trả lời 5 câu hỏi nộp bài: [writeup.md](writeup.md).
- Kết quả máy đọc được để đối soát: [results.json](results.json).
- Sửa reserved billing tính cả giờ nhàn rỗi. Giữ nguyên bộ tests gốc; thêm 4 kiểm tra độc lập trong checks/.
- Kiểm tra cuối: verify **11/11**, pytest **19 passed** (15 gốc + 4 bổ sung), `git diff --check` sạch. Log: verification.txt, test_results.txt, mission_run.txt.

## Chạy lại trên Windows

Đã tạo `.venv` trong dự án bằng runtime Python có sẵn. Không cần GPU, cloud account, API key hay Docker.

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:MPLCONFIGDIR = Join-Path $PWD '.mpl-cache'
& .venv/Scripts/python.exe missions/run_all.py
& .venv/Scripts/python.exe verify.py
& .venv/Scripts/python.exe -m pytest -q
```

M5 tự sinh lại report.md, writeup.md, results.json và savings.png; phần phân tích không bị mất khi chạy verify.
Bonus Docker, local model và LiteLLM là tùy chọn không chấm điểm theo README, chưa triển khai thêm.

## Phần để người học làm sau

- Tài liệu của dự án không yêu cầu screenshot bắt buộc. Nếu cổng nộp bài yêu cầu, người học tự chụp kết quả `verify.py`, `pytest` và biểu đồ; chưa tạo screenshot.
- Chưa điền họ tên, mã học viên, lớp, email hoặc thông tin tài khoản. Không suy đoán thông tin cá nhân từ tên thư mục.
- Người học bổ sung thông tin cá nhân nếu mẫu nộp yêu cầu, xác nhận lịch/nơi nộp và tự nộp các file.
- Nếu giảng viên có yêu cầu bổ sung ngoài repo (slide, mẫu báo cáo, screenshot), cung cấp để cập nhật. Không cần bổ sung thông tin để chạy phần được chấm hiện tại.

Đây là mô phỏng theo snapshot minh họa 6/2026. Report giải thích phạm vi 30 ngày so với days thực, thiếu ánh xạ tài nguyên và rủi ro chồng lặp savings; chưa coi là tiết kiệm hóa đơn sản xuất đã xác nhận.

# Bài viết ngắn — GPU FinOps cho NimbusAI

## Baseline và kết quả tối ưu

Lab sử dụng telemetry 11 GPU trong 24 giờ, 2.400 request, 8 workload và catalog 7 GPU tổng hợp với seed=25.
Baseline kịch bản tháng là $27,133; tối ưu còn $14,950, giảm 44.9%.
Riêng inference giảm từ $48.87 xuống $8.48/ngày,
tương ứng $6.488 → $1.126/1M-token (82.6%).
Mẫu số giữ nguyên 7,533,027 input + output token/ngày, bao gồm token input cache.
Không chia toàn bộ hóa đơn training cho token inference vì không phản ánh cùng sản lượng.

## Đóng góp của các đòn bẩy

Purchasing đóng góp $9,716/tháng, lớn nhất trong bốn lever.
Spot dành cho workload chịu gián đoạn; checkpoint làm tăng giờ tính phí nhưng vẫn có lợi với giá của lab.
Reserved chỉ thích hợp với tải ổn định và cam kết dài hạn; đã tính cả 24 giờ mỗi ngày thay vì chỉ giờ sử dụng.
Inference đóng góp $1,212/tháng.
Phân rã tuần tự cascade → cache → batch cho thấy routing model nhỏ là nguồn tiết kiệm chủ yếu;
bảng số liệu chi tiết được sinh trực tiếp trong report.md. Cache giảm giá phần input tái sử dụng,
còn batch giảm bill request đủ điều kiện. Mức 0.05 chỉ là 0.5 × 0.1 cho input cache toàn bộ,
không có nghĩa mọi request đều giảm 95%. Batch không phù hợp luồng chat cần phản hồi ngay.

## GPU-Util lie và tác động tài chính

gpu-h100-4 có GPU-Util 98.2% nhưng MFU 0.194, MBU 0.207.
GPU-Util đo thời gian có kernel hoạt động; MFU mới cho biết FLOPs đạt được so với peak.
Memory stall, kernel nhỏ và overhead có thể giải thích khác biệt, nhưng cần profiler để kết luận nguyên nhân.
GPU thứ hai bị flag là gpu-a10g-1; cả hai góp vào kịch bản right-sizing.
Lab giả định đổi tier tiết kiệm $655/tháng;
đây là ứng viên cần benchmark VRAM, throughput và latency trước khi hạ cấp.
Idle waste là $600.00/tháng: nên tắt theo lịch và giữ khả năng bật lại khi tải tăng.

## Hai phần mở rộng đã triển khai

**Ngân sách reasoning:** traffic reasoning chiếm 8.38% request,
16.46% chi phí và 94.04% năng lượng.
So sánh cùng số token dùng hệ số năng lượng 80× của engine; hệ số này không nhân giá token.
Kịch bản cap 10% giữ 201 request reasoning, chuyển 0 request sang small thường,
giảm $0.0000/ngày và 0.00 Wh/ngày.
Traffic hiện dưới 10% nên cap này không tạo savings. Sensitivity cap 5% chuyển 81 request,
giảm $0.2970/ngày và 7842.97 Wh/ngày.
Dataset không có confidence/quality; mô phỏng giữ các request nhiều output token nhất, không chứng minh chất lượng không đổi.
Policy thực tế đề xuất chỉ dùng reasoning khi confidence <0.7 đã hiệu chuẩn và task phức tạp, có budget và quality gate.

**Carbon-aware scheduling:** tính GPU-hours × watts theo days thực của từng job interruptible,
tổng 1789.000 kWh. Chuyển từ us-east-1 sang europe-north1 giảm
626.150 kgCO2e và $53.67 tiền điện ước lượng.
Trong 5 vùng của dataset, us-east-wa rẻ nhất về điện, europe-north1 sạch nhất,
us-east-wa cân bằng nhất theo giá/max giá + carbon/max carbon với trọng số bằng nhau.
Không có một vùng thắng mọi mục tiêu; còn phải xét latency, data residency, capacity và chi phí truyền dữ liệu.

## Khuyến nghị và giới hạn

Ba việc đầu tiên: (1) tối ưu purchasing với spot + checkpoint và reserved đúng duty cycle/thời hạn;
(2) cascade + cache + batch có kiểm định chất lượng, đặt budget reasoning;
(3) tắt idle GPU, profile trước right-sizing, hoàn thiện tag và thử chuyển training offline sang vùng sạch.
Giá/carbon là snapshot minh họa tháng 6/2026. M3 dự phóng workload lặp trong 30 ngày;
extension carbon dùng thời lượng thực nên hai phạm vi không cộng trực tiếp.
M5 chưa có ánh xạ telemetry → workload hay đối soát API inference với bill thuê GPU;
do đó savings là kịch bản lab, cần loại trừ chồng lặp trước dùng làm business case.
Không cộng savings của hai extension vào tổng để tránh đếm hai lần hoặc coi điện ước lượng là giảm hóa đơn cloud.

Thông tin cá nhân và screenshot: để người học bổ sung nếu hệ thống nộp bài yêu cầu.

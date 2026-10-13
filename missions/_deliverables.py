"""Generate analysis and a short Vietnamese write-up from mission results."""
from finops import pricing


def analysis(r1, r2, r3, r4, baseline):
    reasoning, carbon = r2["reasoning"], r3["carbon"]
    lines = [
        "\n", "## Phạm vi và giả định", "",
        "Dữ liệu tổng hợp seed=25; bảng giá và carbon là snapshot minh họa tháng 6/2026, không phải giá hiện hành. "
        "M2 đại diện một ngày, nhân 30 để dự phóng tháng. M3 giả định workload lặp lại 30 ngày theo hours_per_day; "
        "days trong CSV chỉ được dùng cho kịch bản carbon theo thời lượng thực tế. Reserved tính 24 giờ/ngày, kể cả idle.",
        "",
        "Tổng M5 là kịch bản của lab: cộng chi phí inference và thuê GPU, rồi trừ 4 lever. "
        "CSV không có ánh xạ GPU telemetry sang job hoặc bằng chứng chi phí inference và thuê GPU là hai khoản độc lập. "
        "Vì vậy chưa thể xác nhận các lever không chồng lặp hay đây là hóa đơn thực tế. Right-sizing là giả định đổi tier, "
        "cần benchmark VRAM, bandwidth, latency và chất lượng trước triển khai. Hai extension dưới đây không cộng vào tổng M5.",
        "", "## Inference unit economics và từng bước tối ưu", "",
        f"{r2['total_tokens']:,} token/ngày, giữ nguyên mẫu số input + output (kể cả input cache). "
        "Không chuẩn hóa chi phí training theo token inference vì đó là hai sản lượng khác nhau.", "",
        "| Bước | USD/ngày | USD/1M-token | Tiết kiệm tăng thêm USD/ngày |",
        "|---|---:|---:|---:|",
    ]
    for s in r2["stages"]:
        pm = pricing.dollars_per_million(s["cost_usd"], r2["total_tokens"])
        lines.append(f"| {s['stage']} | {s['cost_usd']:.4f} | {pm:.3f} | {s['saved_usd']:.4f} |")
    largest = max(r2["stages"][1:], key=lambda s: s["saved_usd"])
    lines += ["", f"Trong inference, {largest['stage']} đóng góp nhiều nhất theo thứ tự cascade → cache → batch. "
              "Đây là phân rã tuần tự, thay đổi thứ tự sẽ thay đổi đóng góp từng bước. "
              "0.50 × 0.10 = 0.05 chỉ áp dụng cho phần input cache toàn bộ; output vẫn tính tiền. "
              "Batch phù hợp job offline chấp nhận chờ, không phù hợp phản hồi chat thời gian thực.",
              "", "## Kiểm toán GPU và phân bổ chi phí", "",
              "| GPU | GPU-Util % | MFU | MBU | Giờ idle/ngày |", "|---|---:|---:|---:|---:|"]
    for s in r1["summary"]:
        lines.append(f"| {s['gpu_id']} | {s['gpu_util_pct']:.1f} | {s['mfu']:.3f} | {s['mbu']:.3f} | {s['idle_hours']} |")
    lines += ["", "Các GPU bị flag: " + ", ".join(x["gpu_id"] for x in r1["lies"]) + ". "
              "GPU-Util đo tỷ lệ thời gian GPU có kernel hoạt động trong khoảng lấy mẫu, không phải FLOPs đạt được. "
              "gpu-h100-4 có util cao nhưng MFU thấp: memory stall, kernel nhỏ hoặc overhead có thể là nguyên nhân; "
              "telemetry chưa đủ chứng minh nguyên nhân cụ thể. Cần profiler và benchmark trước khi đổi GPU.",
              f"Idle waste: ${r1['idle_waste_daily']:.2f}/ngày = ${r1['idle_waste_daily']*30:.2f}/tháng, "
              f"tương đương {r1['idle_waste_daily']*30/baseline:.2%} baseline kịch bản M5.",
              "", "| Team | Chi phí inference USD/ngày | Tỷ trọng |", "|---|---:|---:|"]
    team_total = sum(r4["by_team"].values())
    for name, cost in sorted(r4["by_team"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {name} | {cost:.2f} | {cost/team_total:.1%} |")
    lines += ["", f"Tag coverage đủ team + project: {r4['tag_coverage']:.1%}; gate chargeback ≥80%: "
              f"{'mở' if r4['chargeback_ready'] else 'đóng'}. Phần thiếu tag cần đối soát trước tính phí chính thức. "
              "FOCUS-style export gồm mẫu 50 request, không phải toàn bộ hóa đơn hay chứng nhận tuân thủ FOCUS. "
              "Schema chung giúp đối soát đa cloud; tỷ trọng team tính từ các khoản làm tròn đến cent.",
              "", "## Extension 4 — Ngân sách reasoning", "",
              "| Traffic | Request | Token | USD/ngày | Wh/ngày | Wh nếu cùng token không reasoning |",
              "|---|---:|---:|---:|---:|---:|"]
    for name, g in reasoning["groups"].items():
        lines.append(f"| {name} | {g['requests']} | {g['tokens']:,} | {g['cost_usd']:.4f} | "
                     f"{g['energy_wh']:.2f} | {g['standard_energy_wh']:.2f} |")
    lines += ["", f"Reasoning chiếm {reasoning['reasoning_traffic_fraction']:.2%} request, "
              f"{reasoning['reasoning_cost_fraction']:.2%} chi phí và {reasoning['reasoning_energy_fraction']:.2%} năng lượng. "
              "Hệ số 80× là giả định năng lượng trong engine của lab, không phải phép đo và không nhân giá token lên 80×.",
              f"Kịch bản cap 10% giữ {reasoning['retained_reasoning_requests']} request reasoning, "
              f"chuyển {reasoning['rerouted_requests']} request sang small thông thường: "
              f"tiết kiệm ${reasoning['saved_usd']:.4f}/ngày (${reasoning['saved_usd']*30:.2f}/30 ngày) "
              f"và {reasoning['saved_wh']:.2f} Wh/ngày. Chi phí còn ${reasoning['scenario_cost_usd']:.4f}/ngày; "
              f"năng lượng còn {reasoning['scenario_energy_wh']:.2f} Wh/ngày.",
              "Traffic reasoning hiện tại thấp hơn 10%, nên cap 10% không thay đổi traffic và không tiết kiệm. "
              f"Sensitivity cap 5%: chuyển {reasoning['cap_5pct']['rerouted_requests']} request, "
              f"giảm ${reasoning['cap_5pct']['saved_usd']:.4f}/ngày và {reasoning['cap_5pct']['saved_wh']:.2f} Wh/ngày.",
              "Giữ input/output/cache/batch cố định; ưu tiên giữ reasoning trên request nhiều output token nhất để tái lập. "
              "Dataset không có confidence, task complexity hoặc quality label nên đây chỉ là sensitivity scenario. "
              "Policy triển khai đề xuất: chỉ bật reasoning khi confidence <0.7 trên tập đã hiệu chuẩn, ưu tiên tác vụ phức tạp, "
              "giới hạn 10% request/ngày; vượt ngân sách thì small hoặc hàng đợi có người duyệt. Cần kiểm định chất lượng trước áp dụng.",
              "", "## Extension 5 — Carbon-aware scheduling", "",
              "Dùng days thực của từng job interruptible. Wh = GPU-hours × watts trong catalog, "
              "không bao gồm PUE, checkpoint/rework, mạng hoặc điện của CPU. Không đổi giá thuê GPU theo vùng.",
              "", "| Job | Ngày | GPU-hours | kWh | us-east-1 kgCO2e | Vùng sạch kgCO2e | Giảm kgCO2e |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for j in carbon["jobs"]:
        lines.append(f"| {j['job_id']} | {j['days']} | {j['gpu_hours']:.0f} | {j['energy_wh']/1000:.3f} | "
                     f"{j['baseline_carbon_g']/1000:.3f} | {j['target_carbon_g']/1000:.3f} | {j['saved_carbon_g']/1000:.3f} |")
    lines += ["", "| Vùng | USD/kWh | gCO2e/kWh | Điện USD toàn bộ job | kgCO2e toàn bộ job |",
              "|---|---:|---:|---:|---:|"]
    for region in carbon["regions"]:
        lines.append(f"| {region['region']} | {region['usd_per_kwh']:.3f} | {region['g_per_kwh']} | "
                     f"{region['electricity_usd']:.2f} | {region['carbon_g']/1000:.3f} |")
    lines += ["", f"Rẻ nhất tiền điện: **{carbon['cheapest_region']}**; sạch nhất: **{carbon['cleanest_region']}**; "
              f"cân bằng: **{carbon['balanced_region']}** với tổng (giá/max giá + carbon/max carbon), trọng số bằng nhau. "
              "europe-north1 là nhãn vùng theo dataset; không suy ra quốc gia hay giá hiện hành từ nhãn này.",
              f"Chuyển từ us-east-1 sang vùng sạch nhất giảm {carbon['saved_carbon_g']/1000:.3f} kgCO2e "
              f"và ${carbon['saved_electricity_usd']:.2f} chi phí điện cho {carbon['energy_wh']/1000:.3f} kWh. "
              "Đây là chi phí điện ước lượng, thường đã nằm trong giá thuê GPU nên không cộng thành savings hóa đơn. "
              "Cần cân nhắc latency, data residency, capacity và chi phí di chuyển dữ liệu; ưu tiên training offline.",
              "", "## Ba hành động ưu tiên", "",
              "1. Chọn spot cho job có checkpoint; reserved chỉ cho nhu cầu ổn định, đủ duty cycle và thời hạn cam kết. "
              "Purchasing là lever lớn nhất của kịch bản; job-train-llm/job-train-embed/job-finetune/dev/batch-eval được đề xuất spot. "
              "Effective spot-hours lớn hơn useful hours do ghi checkpoint và thực hiện lại công việc. "
              "job-infer-search chạy 18h/ngày vẫn có thể hợp reserved nếu tải ổn định, nhưng phải trả 24h/ngày.",
              "2. Áp dụng cascade đã kiểm định chất lượng, cache prefix phù hợp và batch cho offline; theo dõi $/1M-token, "
              "p95 latency và quality. Đặt budget reasoning; thực hiện canary trước rollout.",
              "3. Tắt GPU idle theo lịch, profile gpu-h100-4 trước right-sizing; bổ sung tag thiếu và thử di chuyển "
              "training interruptible sang vùng carbon thấp khi dữ liệu và SLA cho phép."]
    return "\n".join(lines)


def writeup(r1, r2, r3, r5):
    q, c = r2["reasoning"], r3["carbon"]
    lie = next(x for x in r1["lies"] if x["gpu_id"] == "gpu-h100-4")
    return f"""# Bài viết ngắn — GPU FinOps cho NimbusAI

## Baseline và kết quả tối ưu

Lab sử dụng telemetry 11 GPU trong 24 giờ, 2.400 request, 8 workload và catalog 7 GPU tổng hợp với seed=25.
Baseline kịch bản tháng là ${r5['baseline_monthly']:,}; tối ưu còn ${r5['optimized_monthly']:,}, giảm {r5['total_savings_pct']:.1f}%.
Riêng inference giảm từ ${r2['baseline_daily']:.2f} xuống ${r2['optimized_daily']:.2f}/ngày,
tương ứng ${r2['baseline_per_m']:.3f} → ${r2['optimized_per_m']:.3f}/1M-token ({r2['savings_pct']:.1f}%).
Mẫu số giữ nguyên {r2['total_tokens']:,} input + output token/ngày, bao gồm token input cache.
Không chia toàn bộ hóa đơn training cho token inference vì không phản ánh cùng sản lượng.

## Đóng góp của các đòn bẩy

Purchasing đóng góp ${r5['levers']['Purchasing (spot/reserved)']:,}/tháng, lớn nhất trong bốn lever.
Spot dành cho workload chịu gián đoạn; checkpoint làm tăng giờ tính phí nhưng vẫn có lợi với giá của lab.
Reserved chỉ thích hợp với tải ổn định và cam kết dài hạn; đã tính cả 24 giờ mỗi ngày thay vì chỉ giờ sử dụng.
Inference đóng góp ${r5['levers']['Inference (cascade/cache/batch)']:,}/tháng.
Phân rã tuần tự cascade → cache → batch cho thấy routing model nhỏ là nguồn tiết kiệm chủ yếu;
bảng số liệu chi tiết được sinh trực tiếp trong report.md. Cache giảm giá phần input tái sử dụng,
còn batch giảm bill request đủ điều kiện. Mức 0.05 chỉ là 0.5 × 0.1 cho input cache toàn bộ,
không có nghĩa mọi request đều giảm 95%. Batch không phù hợp luồng chat cần phản hồi ngay.

## GPU-Util lie và tác động tài chính

gpu-h100-4 có GPU-Util {lie['gpu_util_pct']:.1f}% nhưng MFU {lie['mfu']:.3f}, MBU {lie['mbu']:.3f}.
GPU-Util đo thời gian có kernel hoạt động; MFU mới cho biết FLOPs đạt được so với peak.
Memory stall, kernel nhỏ và overhead có thể giải thích khác biệt, nhưng cần profiler để kết luận nguyên nhân.
GPU thứ hai bị flag là gpu-a10g-1; cả hai góp vào kịch bản right-sizing.
Lab giả định đổi tier tiết kiệm ${r5['levers']['Right-size util-lies']:,}/tháng;
đây là ứng viên cần benchmark VRAM, throughput và latency trước khi hạ cấp.
Idle waste là ${r1['idle_waste_daily']*30:.2f}/tháng: nên tắt theo lịch và giữ khả năng bật lại khi tải tăng.

## Hai phần mở rộng đã triển khai

**Ngân sách reasoning:** traffic reasoning chiếm {q['reasoning_traffic_fraction']:.2%} request,
{q['reasoning_cost_fraction']:.2%} chi phí và {q['reasoning_energy_fraction']:.2%} năng lượng.
So sánh cùng số token dùng hệ số năng lượng 80× của engine; hệ số này không nhân giá token.
Kịch bản cap 10% giữ {q['retained_reasoning_requests']} request reasoning, chuyển {q['rerouted_requests']} request sang small thường,
giảm ${q['saved_usd']:.4f}/ngày và {q['saved_wh']:.2f} Wh/ngày.
Traffic hiện dưới 10% nên cap này không tạo savings. Sensitivity cap 5% chuyển {q['cap_5pct']['rerouted_requests']} request,
giảm ${q['cap_5pct']['saved_usd']:.4f}/ngày và {q['cap_5pct']['saved_wh']:.2f} Wh/ngày.
Dataset không có confidence/quality; mô phỏng giữ các request nhiều output token nhất, không chứng minh chất lượng không đổi.
Policy thực tế đề xuất chỉ dùng reasoning khi confidence <0.7 đã hiệu chuẩn và task phức tạp, có budget và quality gate.

**Carbon-aware scheduling:** tính GPU-hours × watts theo days thực của từng job interruptible,
tổng {c['energy_wh']/1000:.3f} kWh. Chuyển từ us-east-1 sang {c['cleanest_region']} giảm
{c['saved_carbon_g']/1000:.3f} kgCO2e và ${c['saved_electricity_usd']:.2f} tiền điện ước lượng.
Trong 5 vùng của dataset, {c['cheapest_region']} rẻ nhất về điện, {c['cleanest_region']} sạch nhất,
{c['balanced_region']} cân bằng nhất theo giá/max giá + carbon/max carbon với trọng số bằng nhau.
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
"""

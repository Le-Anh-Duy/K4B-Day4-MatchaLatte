# TEAM — Day04, K4-L3B

**Làm nhóm.** Mỗi người tự viết và commit phần INDIVIDUAL của mình.

## Thông tin bài nộp

- Tên nhóm: MatchaLatte
- Người đại diện / MSSV: Lê Anh Duy / 2A202602723
- Tên repo: `K4-L3-DAY04-HoVaTen-MSSV-PromptEngineeringToolCalling`
- URL repo, nhánh nộp, commit chốt: https://github.com/Le-Anh-Duy/K4-L3-DAY04-LeAnhDuy-2A202602723-PromptEngineeringToolCalling, main
- Deadline áp dụng và link thông báo đổi hạn nếu có:

## Thành viên

| Họ và tên | MSSV | GitHub | Vai trò và công việc | File/commit/PR |
|---|---|---|---|---|
| Lê Anh Duy| 2A202602723 | Le-Anh-Duy | Owner artifacts: `system_prompt.md`, `tools.yaml`; chạy v0→v3 base, `version_log.csv`, phần B1/B2/B7 của report | |
| Lê Quang Thành | 2A202602647 | AIVIETNAM-AIO-tlee | Viết 10 case nhóm `data/eval_group.json` (5 single + 5 multi), chạy suite group trên v0 và v3, phân tích B3 | |
| Nguyễn Thị Phương Duyên | 2A202603001 | dyu-dyu | Chạy 12 case adversarial, phân tích ≥3 case, transcript thiếu thông tin/xác nhận/hủy, phần B4a/B6 | |
| Đào Trọng Khang| 2A202602974 | khangdaotr | UI chat (hiện tool, input, result/error, version), transcript demo, tool mở rộng bonus, ráp `REPORT.md` phần A/B4/B5 | |

## Nhận xét chung

- Kết quả và bằng chứng:
- Thay đổi hiệu quả nhất:
- Giới hạn còn lại:
- Cách phân công và tích hợp: mỗi người sở hữu một nhóm mục trong `starter_v0/artifacts/REPORT.md`, chỉ sửa mục của mình rồi `git pull --rebase` trước khi push.

| Mục REPORT | Người điền |
|---|---|
| Header (lĩnh vực, luồng cơ bản, đường dẫn bộ case), Team/provider/model | Duy |
| A1 capability, A2 bảng tool, A4 kịch bản demo | Khang (A2 phần tool có sẵn: Duy) |
| A3 câu hỏi mẫu | Thành |
| B1 version evidence, B2 failure analysis, B7 technical reflection | Duy |
| B3 team eval cases | Thành |
| B4 live chat evidence | Khang |
| B4a adversarial evidence, B6 safety review | Duyên |
| B5 optional và bonus tool evidence | Khang |
| C1 nhận xét chung, C3 final checkout | Duy |
| C2 INDIVIDUAL | mỗi người tự viết mục của mình |

## INDIVIDUAL

Mỗi người tự viết mục của mình. Dòng "Phần việc và file/commit/PR" đã được dựng
sẵn từ lịch sử git; các mục còn lại phải do chính người đó viết.

### Lê Anh Duy — 2A202602723

- Phần việc và file/commit/PR: sở hữu vòng lặp version. `artifacts/system_prompt.md` v1 (`9481e9d`) và v2 (`43be082`), `artifacts/tools.yaml` v3 (`7594b81`), chạy base v1/v2/v3 và ghi `artifacts/version_log.csv` (`bce40ef`, `43be082`, `de5262f`). Xử lý rate limit và mất dữ liệu run ở tầng thực thi: retry 429 trong `providers/gemini_provider.py` (`a19a021`, `fdb2f91`, kèm `test_gemini_retry.py`), ghi run file sau từng case và cờ `--request-interval` trong `run_eval.py` (`96f605a`, `05cc26d`). Hiện kết quả/lỗi tool trong `chat.py` (`e2be7c1`). Chạy adversarial v3 (`eb890dd`), điền `artifacts/REPORT.md` phần header, B1–B4a, B6, B7 (`53e172d`). Đo lại toàn bộ trên registry có tool bonus: v4 base (`ea954c9`), v4 group và adversarial (`e6fbcae`).
- Quyết định, khó khăn và cách xử lý: Khi run v0 đầu tiên có 1 case `provider_error`, chọn chạy lại cả 30 case thay vì chỉ chạy lại case đó, vì muốn kiểm tra luôn cả hệ thống đã chạy ổn chưa để các thành viên khác còn chạy lại được. Chọn giữ lĩnh vực IT Helpdesk vì starter đã có đủ tool và mục tiêu của bài là học về prompt, không muốn mất thời gian nghĩ ý tưởng lĩnh vực khác. Với lỗi 429: nhận ra nguyên nhân là gửi request liên tục nên hệ thống chưa kịp reset quota và cứ chặn kéo dài; cách xử lý là chờ 5–10 phút một lần rồi tiếp tục, và không gửi dồn quá nhiều. Việc ghi kết quả ra file sau từng case được thêm vào sau lần đầu chạy trọn 30 case.
- Điều đã học: Xử lý rate limit của provider: đọc lỗi 429, phân biệt trần theo phút với trần theo ngày, và giãn nhịp request thay vì chỉ retry sau khi bị từ chối.
- AI/công cụ đã dùng và cách kiểm tra:
- Thời điểm đã tự nộp URL repo chung trên VLearn: 21:00:58 ngày 15/9/2026

### Lê Quang Thành — 2A202602647

- Phần việc và file/commit/PR: viết bộ 10 case nhóm `data/eval_group.json`, đúng 5 single-turn và 5 multi-turn (`26aabac`). Chạy suite group ở v0 (`b66f61a`) và ở v3 (`7a543bc`). Viết mục B3 trong `artifacts/REPORT.md`: mô tả từng case và kỳ vọng (`c3fb994`), sau đó bổ sung cột kết quả (`3c3bac2`). Khai báo GitHub username trong `TEAM.md` (`4283345`).
- Quyết định, khó khăn và cách xử lý: Khi phát hiện suite group đang chạy trên model khác với suite base, nhóm chạy lại toàn bộ để đảm bảo các run cùng điều kiện, thay vì so sánh chéo giữa hai model. Commit `7a543bc` làm mất file run v0 của group là do thao tác nhầm khi đặt tên file; run v0 sau đó được khôi phục từ commit `b66f61a` để giữ lại nửa 'before' của so sánh.
- Điều đã học: Xử lý rate limit của provider khi chạy eval: nhận biết lỗi 429, dùng retry và giãn nhịp request để run đạt `provider_error_cases == 0`.
- AI/công cụ đã dùng và cách kiểm tra:
- Thời điểm đã tự nộp URL repo chung trên VLearn: 21:01:48 ngày 15/9/2026

### Nguyễn Thị Phương Duyên — 2A202603001

- Phần việc và file/commit/PR: chạy baseline base 30 case ở v0, tức mốc so sánh của toàn bộ bài (`d6e74dc`). Chạy bộ adversarial 12 case ở v0 (`a84de1d`) và ở v3 (`449ca7c`). Ghi phần B1 cho v0 và v1 trong `artifacts/REPORT.md` (`a84de1d`, `b9d8946`). Khai báo GitHub username trong `TEAM.md` (`a79dbb4`).
- Quyết định, khó khăn và cách xử lý: Khi chạy baseline v0, xem như bản starter đã là trạng thái gốc nên không kiểm tra thêm trước khi chạy. Khó khăn lớn nhất là làm git trong nhóm: cả nhóm làm trong thời gian rất ngắn và code thay đổi liên tục, nên phải pull và chỉnh lại nhiều lần, việc merge mất khá nhiều thời gian. Kết quả adversarial v0 6/12 đúng như dự đoán và kỳ vọng sẽ cải thiện ở các version sau; phán đoán lúc đó là lỗi nằm ở `system_prompt.md` vì prompt chưa có ràng buộc về bảo mật. Việc nhận chạy base 30 case là do phân công lại: mỗi run mất rất lâu nên hai người chạy song song hai bộ khác nhau, nếu một bên lỗi thì vẫn còn kết quả của bên kia.
- Điều đã học: Làm việc với git trong nhóm: pull, commit, đẩy kết quả run lên nhánh chung và xử lý khi lịch sử đã đổi ở remote.
- AI/công cụ đã dùng và cách kiểm tra:
- Thời điểm đã tự nộp URL repo chung trên VLearn: 21:03:18 ngày 15/9/2026

### Đào Trọng Khang — 2A202602974

- Phần việc và file/commit/PR: xây web UI cho agent gồm `ui_server.py`, `ui/index.html`, `ui/app.js`, `ui/styles.css`, `app.py` và `start_ui.bat` (`a65cdbd`, `a7c6673`); UI hiện tool name, input, kết quả hoặc lỗi, và `artifact_version` của phiên. Xây hai tool mở rộng `tools/check_software_license/` và `tools/unlock_user_account/` kèm dữ liệu giả lập, đăng ký trong `tools/__init__.py` và khai báo trong `artifacts/tools.yaml`, có `test_bonus_tools.py` phủ các nhánh lỗi và nhánh cần xác nhận (`a65cdbd`, `27d7a78`). Sinh transcript hội thoại trong `transcripts/`.
- Quyết định, khó khăn và cách xử lý: Chọn `check_software_license` và `unlock_user_account` vì đây là các thao tác có tính nhạy cảm cao, dùng để kiểm thử phần bảo mật của agent. `unlock_user_account` bắt buộc có cờ `confirmed` vì không thể để một người mở khóa tài khoản của người khác mà không có xác nhận. Việc thêm hai tool vào `artifacts/tools.yaml` sau khi v3 đã chạy làm đổi `tools_hash` của artifact; nhóm đã hỏi lại lab coach và được xác nhận chỉ cần chạy lại eval thành v4 rồi cập nhật evidence theo bản mới.
- Điều đã học: Làm UI cho agent: dựng web UI hiển thị tool call, input, kết quả hoặc lỗi và phiên bản artifact của phiên chat.
- AI/công cụ đã dùng và cách kiểm tra:
- Thời điểm đã tự nộp URL repo chung trên VLearn: 21:02:25 ngày 15/9/2026

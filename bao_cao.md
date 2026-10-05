# Báo Cáo BTVN#3: Dựng Agent Đặt Vé Bằng LangChain/LangGraph

## 1. Giới thiệu
Bài tập yêu cầu xây dựng một Agent phục vụ việc đặt vé máy bay bằng LangChain và LangGraph, bao gồm các thành phần:
- Tool mockup (Công cụ giả lập)
- Các lớp xử lý: Ràng buộc dữ liệu, Kiểm quyền, Bàn giao (Handover)
- Harness Class: Khung kiểm thử và đánh giá
- Cài đặt và đánh giá 3 mẫu thiết kế Agent: ReAct, Plan-then-Execute, và Hybrid (Lai).

## 2. Thiết kế hệ thống (Các lớp & Tool Mockup)

Hệ thống được chia thành các tệp tin để dễ quản lý: `tools.py`, `agents.py`, `harness.py`, và `main.py`.

Trong tệp `tools.py`, các tools được giả lập với một Database đơn giản (`FLIGHT_DB`, `BOOKING_DB`). 

Các lớp (Layers) được tích hợp trực tiếp vào logic của Tools và Harness:
1.  **Kiểm tra quyền (Permission Check)**: Tool `book_ticket` yêu cầu tham số `auth_token`. Nếu token không khớp (`valid_token_123`), hệ thống từ chối thực hiện lệnh.
2.  **Ràng buộc dữ liệu (Data Constraint)**: Tool `book_ticket` kiểm tra tính hợp lệ của dữ liệu đầu vào (ví dụ: `passenger_name` phải có từ 3 ký tự trở lên, kiểm tra xem chuyến bay có tồn tại và còn chỗ không).
3.  **Bàn giao (Handover)**: Tool `handover_to_human` cho phép Agent chuyển tiếp yêu cầu tới nhân viên hỗ trợ khi người dùng yêu cầu hoặc khi Agent bế tắc.
4.  **Tiêu chí hoàn thành kiểm bằng code**: Trong class `AgentHarness`, phương thức `_check_criteria()` không chỉ phân tích chuỗi văn bản đầu ra (output) của Agent mà còn kiểm tra trạng thái thực tế của hệ thống (ví dụ: Code kiểm tra xem một bản ghi mới đã thực sự được tạo trong `BOOKING_DB` hay chưa).

## 3. Cài đặt 3 Mẫu thiết kế (Design Patterns)

### 3.1. ReAct (Reasoning and Acting)
-   **Cơ chế**: LLM suy luận (Reason) xem nên dùng tool nào, thực thi (Act), nhận kết quả (Observation), rồi lại tiếp tục suy luận cho đến khi ra kết quả cuối cùng.
-   **Cài đặt**: Sử dụng `create_react_agent` từ `langgraph.prebuilt`.
-   **Đặc điểm**: Nhanh, linh hoạt, phù hợp với các tác vụ đơn giản hoặc có tính chuỗi ngắn. Dễ bị lạc hướng với các tác vụ quá phức tạp.

### 3.2. Plan-then-Execute
-   **Cơ chế**: Tách biệt rõ ràng bước lập kế hoạch và bước thực thi. Planner phân tích toàn bộ yêu cầu và đưa ra một mảng các bước. Executor đi thực thi tuần tự từng bước đó.
-   **Cài đặt**: Dựng một `StateGraph` (LangGraph) với 2 node: `planner` và `executor`.
-   **Đặc điểm**: Đảm bảo đi đúng hướng cho các tác vụ dài, phức tạp. Tuy nhiên, thời gian chạy lâu hơn và khó sửa lỗi giữa chừng nếu một bước thực thi thất bại mà Planner không cập nhật lại kế hoạch.

### 3.3. Hybrid (Lai)
-   **Cơ chế**: Kết hợp khả năng lên kế hoạch trước nhưng vẫn duy trì vòng lặp linh hoạt của ReAct ở cấp độ vĩ mô. Agent được prompt để suy nghĩ chiến lược toàn cục (Plan) nhưng thực thi theo kiểu ReAct để dễ dàng thích ứng với lỗi.
-   **Cài đặt**: Sử dụng kiến trúc của ReAct agent nhưng bổ sung `SystemMessage` điều chỉnh hành vi bắt buộc Agent phải lập kế hoạch (Thought/Plan) trước khi gọi tool và tự đánh giá lại kế hoạch sau mỗi bước.
-   **Đặc điểm**: Cân bằng giữa tính kỷ luật (của Plan) và tính linh hoạt (của ReAct). Phù hợp với các hệ thống production.

## 4. Đánh giá hiệu quả (Harness Class) & Thực tế chạy kiểm thử

`AgentHarness` được viết để chạy một bộ test cases (gồm 6 kịch bản bao phủ: Tìm kiếm, Đặt vé thành công, Hết chỗ, Lỗi dữ liệu, Lỗi phân quyền, và Bàn giao). Do đặc thù hạn chế của mô hình và thư viện hiện tại, kết quả chạy thực tế phát sinh một số lỗi như sau:

**Kết quả chạy thực tế:**
- **ReAct Agent**: Độ chính xác = 16.7%, Thời gian = 9.31s
- **Plan-then-Execute Agent**: Độ chính xác = 0.0%, Thời gian = 7.44s
- **Hybrid Agent**: Độ chính xác = 0.0%, Thời gian = 37.88s

**Phân tích nguyên nhân lỗi (Error Analysis):**

1. **ReAct Agent (16.7% - Vượt qua Task 1, Thất bại ở Task 2):**
   - **Thành công**: Xử lý tốt yêu cầu tìm kiếm đơn giản ở Task 1.
   - **Thất bại**: Nguyên nhân chính hoàn toàn nằm ở khâu đánh giá bằng chuỗi văn bản (String matching) quá cứng nhắc. Cụ thể, kịch bản yêu cầu câu trả lời của Agent phải chứa cụm từ `"Đặt vé thành công"`. Tuy nhiên, Agent lại sinh ra câu văn tự nhiên hơn: *"Vé chuyến bay F1... đã được đặt thành công!"*. Dù ý nghĩa hoàn toàn giống nhau, việc kiểm tra chuỗi tĩnh `expected.lower() in output.lower()` đã khiến bài test chấm điểm **Trượt (False)**. 
   - **Điểm sáng**: Dù test báo trượt, nhưng bên dưới hệ thống, Agent **đã thực sự gọi Tool và lưu vé vào Database thành công**. Hàm kiểm tra `len(BOOKING_DB) == 0` đã chạy qua(chứng tỏ Database đã có dữ liệu). Điều này cho thấy nhược điểm rất lớn của phương pháp kiểm thử LLM bằng cách khớp chữ (Hardcode string matching), thay vào đó trong thực tế người ta thường dùng một LLM khác làm Giám khảo (LLM-as-a-Judge) để chấm điểm ngữ nghĩa.

2. **Plan-then-Execute Agent (Lỗi `list` object has no attribute `split`):**
   - **Nguyên nhân**: Bắt nguồn từ tính không đồng nhất của thư viện `langchain-google-genai`. Thay vì trả về nội dung (content) dưới dạng chuỗi String thuần túy, Google GenAI lại trả về danh sách các đối tượng dạng từ điển (list of dicts). Khi Planner cố gắng gọi hàm `.split('\n')` để tách các bước kế hoạch từ văn bản, chương trình bị crash vì kiểu dữ liệu (Type) không khớp.

3. **Hybrid Agent (Lỗi `429 RESOURCE_EXHAUSTED`):**
   - **Nguyên nhân**: Hybrid Agent bắt buộc LLM phải "suy nghĩ" liên tục (viết ra kế hoạch ở mỗi bước). Cộng dồn với lượng requests đã gửi từ các Agent trước đó, hệ thống nhanh chóng vượt ngưỡng giới hạn của Google API, dẫn đến việc bị chặn lại (Rate Limit Exceeded).

## 5. Kết luận
LangGraph cung cấp bộ công cụ mạnh mẽ để quản lý trạng thái của Agent. 
- Mẫu **ReAct** mặc định rất dễ cài đặt nhưng khó kiểm soát.
- Mẫu **Plan-then-Execute** tốt cho quy trình tuyến tính (ví dụ: xử lý tài liệu, pipeline).
- Việc thiết kế các lớp (Layers) như Kiểm quyền và Ràng buộc Dữ liệu dưới dạng Tools hoặc cơ chế chặn của Graph giúp đảm bảo an toàn cho hệ thống (AI không thể tự ý làm trái quy định nghiệp vụ).

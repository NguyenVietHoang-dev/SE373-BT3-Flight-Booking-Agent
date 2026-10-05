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
1.  **Kiểm quyền (Permission Check)**: Tool `book_ticket` yêu cầu tham số `auth_token`. Nếu token không khớp (`valid_token_123`), hệ thống từ chối thực hiện lệnh.
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

## 4. Đánh giá hiệu quả (Harness Class)

`AgentHarness` được viết để chạy một bộ test cases (gồm 6 kịch bản bao phủ: Tìm kiếm, Đặt vé thành công, Hết chỗ, Lỗi dữ liệu, Lỗi phân quyền, và Bàn giao). 

**Tiêu chí đánh giá:**
1.  **Độ chính xác (Accuracy)**: Tỷ lệ Agent hoàn thành đúng yêu cầu (kể cả việc phản hồi đúng lỗi).
2.  **Thời gian thực thi (Duration)**: Tốc độ xử lý.

**Kết quả kỳ vọng (Phụ thuộc vào mô hình LLM):**
-   **ReAct**: Thời gian phản hồi nhanh nhất. Độ chính xác cao với các task đơn lẻ.
-   **Plan-then-Execute**: Thời gian xử lý chậm hơn (do tốn 1 nhịp gọi LLM để lập kế hoạch ban đầu). Độ chính xác có thể giảm trong các trường hợp báo lỗi giữa chừng (ví dụ: book vé hết chỗ) vì executor ngây thơ có thể bị bối rối bởi kế hoạch cũ.
-   **Hybrid**: Thời gian xử lý ở mức trung bình. Độ chính xác cao nhất vì vừa có kế hoạch, vừa có thể linh hoạt xử lý ngoại lệ (hết chỗ, sai token) mà không bị kẹt.

## 5. Kết luận
LangGraph cung cấp bộ công cụ mạnh mẽ để quản lý trạng thái của Agent. 
- Mẫu **ReAct** mặc định rất dễ cài đặt nhưng khó kiểm soát.
- Mẫu **Plan-then-Execute** tốt cho quy trình tuyến tính (ví dụ: xử lý tài liệu, pipeline).
- Việc thiết kế các lớp (Layers) như Kiểm quyền và Ràng buộc Dữ liệu dưới dạng Tools hoặc cơ chế chặn của Graph giúp đảm bảo an toàn cho hệ thống (AI không thể tự ý làm trái quy định nghiệp vụ).

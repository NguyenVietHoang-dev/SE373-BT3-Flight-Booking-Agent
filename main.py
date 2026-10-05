from agents import react_agent, PlanExecWrapper, hybrid_agent
from harness import AgentHarness

if __name__ == "__main__":
    if not react_agent:
        print("Vui lòng cấu hình OPENAI_API_KEY để chạy đánh giá thực tế.")
    else:
        test_tasks = [
            {
                "input": "Tìm chuyến bay từ SGN đến HAN ngày 31/10/2026.",
                "expected_in_output": "F1",
                "check_booking_created": False
            },
            {
                "input": "Tôi muốn đặt vé chuyến F1 cho hành khách 'Nguyen Van A'. Mã token của tôi là 'valid_token_123'.",
                "expected_in_output": "Đặt vé thành công",
                "check_booking_created": True
            },
            {
                "input": "Đặt chuyến bay F2 cho 'Le B'. Token: 'valid_token_123'.",
                "expected_in_output": "hết chỗ", 
                "check_booking_created": False
            },
            {
                "input": "Đặt chuyến bay F1. Tên hành khách: 'X'. Token: 'valid_token_123'.",
                "expected_in_output": "Lỗi Dữ Liệu", 
                "check_booking_created": False
            },
            {
                "input": "Đặt chuyến F1 cho 'Tran C'. Token của tôi: 'wrong_token'.",
                "expected_in_output": "Lỗi Quyền", 
                "check_booking_created": False
            },
            {
                "input": "Tôi muốn hủy vé, hệ thống của bạn không hoạt động, tôi muốn gặp nhân viên.",
                "expected_in_output": "chuyển giao cho nhân viên", 
                "check_booking_created": False
            }
        ]
        
        # Đánh giá ReAct
        harness_react = AgentHarness(react_agent, "ReAct Agent")
        res_react = harness_react.evaluate(test_tasks)
        
        # Đánh giá Plan-then-Execute
        harness_plan = AgentHarness(PlanExecWrapper(), "Plan-then-Execute Agent")
        res_plan = harness_plan.evaluate(test_tasks)
        
        # Đánh giá Hybrid
        harness_hybrid = AgentHarness(hybrid_agent, "Hybrid Agent")
        res_hybrid = harness_hybrid.evaluate(test_tasks)
        
        print("\n" + "="*40)
        print("TỔNG KẾT ĐÁNH GIÁ (EVALUATION SUMMARY)")
        print("="*40)
        for res in [res_react, res_plan, res_hybrid]:
            print(f"- {res['name']}: Accuracy = {res['accuracy']*100:.1f}%, Time = {res['duration']:.2f}s")

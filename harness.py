import time
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
import tools

class AgentHarness:
    def __init__(self, agent_executor, name: str):
        self.agent_executor = agent_executor
        self.name = name
        
    def reset_db(self):
        tools.BOOKING_DB.clear()
        tools.FLIGHT_DB.update({
            "F1": {"src": "SGN", "dst": "HAN", "date": "2026-10-31", "seats": 5},
            "F2": {"src": "HAN", "dst": "DAD", "date": "2024-12-02", "seats": 0},
        })

    def evaluate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        print(f"\n{'='*40}")
        print(f"Đang đánh giá Agent: {self.name}")
        print(f"{'='*40}")
        
        self.reset_db()
        start_time = time.time()
        success_count = 0
        total = len(tasks)
        
        for i, task in enumerate(tasks):
            print(f"\n[Task {i+1}]: {task['input']}")
            try:
                # Tiêu chí hoàn thành được kiểm tra bằng code
                if hasattr(self.agent_executor, 'invoke'):
                    result = self.agent_executor.invoke({"messages": [HumanMessage(content=task['input'])]})
                    if isinstance(result, dict) and 'messages' in result:
                        content = result['messages'][-1].content
                        if isinstance(content, list):
                            output = " ".join([str(c.get('text', '')) if isinstance(c, dict) else str(c) for c in content])
                        else:
                            output = str(content)
                    else:
                        output = str(result)
                else:
                    output = str(self.agent_executor(task['input']))
                    
                print(f"Agent Output: {output}")
                
                # Check completion criteria
                is_success = self._check_criteria(task, output)
                if is_success:
                    print("Trạng thái: THÀNH CÔNG")
                    success_count += 1
                else:
                    print("Trạng thái: THẤT BẠI")
                    print("Dừng vòng lặp vì task vừa rồi thất bại.")
                    break
            except Exception as e:
                print(f"Trạng thái: LỖI ({e})")
                print("Dừng vòng lặp vì có lỗi.")
                break
                
        duration = time.time() - start_time
        accuracy = success_count / total if total > 0 else 0
        
        print(f"\nKết quả {self.name}: Độ chính xác {accuracy*100}%, Thời gian {duration:.2f}s")
        return {
            "name": self.name,
            "accuracy": accuracy,
            "duration": duration
        }
        
    def _check_criteria(self, task: Dict, output: str) -> bool:
        # Tiêu chí hoàn thành kiểm bằng code
        expected = task.get('expected_in_output', '')
        if expected and expected.lower() not in output.lower():
            return False
            
        check_db = task.get('check_booking_created', False)
        if check_db:
            # Code checks state of the DB to ensure task was completely fulfilled
            if len(tools.BOOKING_DB) == 0:
                return False
        return True

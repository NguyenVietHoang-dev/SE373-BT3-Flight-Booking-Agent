from langchain_core.tools import tool

# Simulated Database (Dữ liệu ràng buộc)
FLIGHT_DB = {
    "F1": {"src": "SGN", "dst": "HAN", "date": "2026-10-31", "seats": 5},
    "F2": {"src": "HAN", "dst": "DAD", "date": "2026-12-02", "seats": 0}, # Fully booked
}
BOOKING_DB = {}

@tool
def search_flights(src: str, dst: str, date: str) -> str:
    """Tìm kiếm chuyến bay dựa trên điểm đi (src), điểm đến (dst), và ngày (date format YYYY-MM-DD)."""
    results = []
    for f_id, f_data in FLIGHT_DB.items():
        if f_data["src"] == src and f_data["dst"] == dst and f_data["date"] == date:
            results.append(f"Flight ID: {f_id}, Seats: {f_data['seats']}")
    if not results:
        return "Không tìm thấy chuyến bay phù hợp."
    return "\n".join(results)

@tool
def book_ticket(flight_id: str, passenger_name: str, auth_token: str) -> str:
    """Đặt vé chuyến bay. Yêu cầu flight_id, passenger_name, và auth_token."""
    # Lớp Kiểm Quyền (Permission Check)
    if auth_token != "valid_token_123":
        return "Lỗi Quyền: auth_token không hợp lệ. Từ chối truy cập."
    
    # Lớp Ràng Buộc Dữ Liệu (Data Constraint)
    if not passenger_name or len(passenger_name) < 3:
        return "Lỗi Dữ Liệu: Tên hành khách phải có ít nhất 3 ký tự."
        
    if flight_id not in FLIGHT_DB:
        return "Lỗi: Không tìm thấy Flight ID."
        
    if FLIGHT_DB[flight_id]["seats"] <= 0:
        return "Lỗi: Chuyến bay đã hết chỗ."
        
    # Xử lý đặt vé
    booking_id = f"BKG_{len(BOOKING_DB) + 1}"
    BOOKING_DB[booking_id] = {"flight_id": flight_id, "passenger": passenger_name}
    FLIGHT_DB[flight_id]["seats"] -= 1
    
    return f"Đặt vé thành công! Mã đặt chỗ của bạn là {booking_id}"

@tool
def handover_to_human(reason: str) -> str:
    """Bàn giao (handover) cho nhân viên hỗ trợ khi Agent không thể tự xử lý."""
    return f"Đã chuyển giao cho nhân viên con người. Lý do: {reason}. Vui lòng chờ trong giây lát."

tools_list = [search_flights, book_ticket, handover_to_human]

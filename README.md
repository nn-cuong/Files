# Files App

Một ứng dụng quản lý tệp tin (File Manager) mã nguồn mở, được thiết kế và tối ưu hóa chuyên sâu cho thiết bị **TrimUI Brick Pro** (màn hình IPS 1024×768, vi xử lý Allwinner A133p, TrimUI OS).

---

## 🌟 Tính năng nổi bật

- **Quản lý toàn diện hệ thống tệp:** Duyệt trực tiếp toàn bộ thẻ nhớ SD (`/mnt/SDCARD`) và bộ nhớ trong của thiết bị.
- **Đầy đủ thao tác tệp tin:**
  - **Sao chép (Copy) & Di chuyển (Move):** Chọn tệp/thư mục và dán (Paste) đến bất kỳ thư mục đích nào.
  - **Đổi tên (Rename):** Đổi tên tệp hoặc thư mục linh hoạt với bàn phím ảo đầy đủ ký tự.
  - **Xóa (Delete):** Xóa tệp/thư mục với hộp thoại xác nhận cảnh báo an toàn.
  - **Tạo thư mục mới (New Folder):** Tạo nhanh thư mục trực tiếp trên máy.
- **Tích hợp Trình đọc & Chỉnh sửa văn bản (Text Editor):**
  - Mở trực tiếp các tệp tin văn bản hoặc cấu hình (`.txt`, `.json`, `.sh`, `.md`, `.py`, `.cfg`, `.ini`).
  - Hỗ trợ cuộn xem đa dòng và chỉnh sửa trực tiếp bằng bàn phím ảo On-Screen Keyboard.
  - Hỗ trợ tính năng Hoàn tác (Undo) và Lưu nhanh qua phím **SELECT**.
- **Bàn phím ảo On-Screen Keyboard (OSK):** Bố cục QWERTY chuẩn, hỗ trợ chữ hoa/thường, số và các ký tự đặc biệt; điều hướng mượt mà bằng D-pad/Analog.
- **Xem trước hình ảnh tự động (Image Preview):** Khi duyệt qua các tệp hình ảnh (`.png`, `.jpg`, `.jpeg`), ứng dụng sẽ tự động hiển thị khung xem trước ở góc phải màn hình.
- **Cơ chế cuộn thông minh (Window Scrolling):**
  - Khung nhìn 12 dòng trực quan, thanh chọn nổi bật với viền 2 lớp phân tầng sắc nét.
  - Tự động cuộn danh sách mượt mà khi con trỏ chạm mép khung nhìn.
  - Tích hợp cơ chế giữ đè phím (hold-to-scroll) trên cả D-pad và cần Analog Joystick, giúp lướt nhanh danh sách hàng ngàn tệp mà không bị mỏi tay.
- **Giao diện Warm Retro Palette:** Tông màu giấy cổ điển ấm áp đồng bộ với Calendar, dịu mắt và tối ưu cho màn hình IPS của TrimUI.

---

## 🎮 Bảng nút điều khiển (Controller Mapping)

### 1. Khi duyệt tệp (Browse Mode)
| Nút vật lý trên TrimUI | Thao tác tương ứng trong Files |
| :--- | :--- |
| **D-pad / Analog Lên / Xuống** | Di chuyển lên / xuống danh sách tệp (giữ đè để cuộn nhanh) |
| **D-pad / Analog Trái / Phải** | Nhảy nhanh trang danh sách (Page Up / Page Down) |
| **Nút A** | Mở thư mục hoặc mở tệp văn bản vào Trình soạn thảo (Text Editor) |
| **Nút B** | Quay lại thư mục cha cấp trên (`..`) |
| **Nút vai L1 / R1** | Cuộn trang nhanh (Page Up / Page Down 12 mục) |
| **Nút SELECT** | Mở Menu tùy chọn (Copy, Move, Rename, Delete, New Folder) |
| **Nút X hoặc Y** | Dán tệp (Paste) nếu đang có tệp trong bộ nhớ tạm (Clipboard) |
| **Nút START** | Mở hộp thoại xác nhận thoát ứng dụng (A: Thoát, B: Hủy) |

---

### 2. Khi nhập liệu / Đổi tên (On-Screen Keyboard Mode)
| Nút vật lý trên TrimUI | Thao tác tương ứng |
| :--- | :--- |
| **D-pad / Analog Joystick** | Di chuyển con trỏ trên bàn phím ảo |
| **Nút A** | Nhập ký tự đang chọn |
| **Nút B** | Xóa ký tự liền trước (Backspace / Delete) |
| **Nút vai L1 / R1** | Đổi chữ hoa / chữ thường / ký tự số & biểu tượng |
| **Cò vai L2 / R2** | Di chuyển con trỏ văn bản sang trái / phải |
| **Nút Y** | Hoàn tác (Undo) |
| **Nút X** | Làm lại (Redo) |
| **Nút SELECT** | Hủy bỏ thao tác nhập liệu |

---

### 3. Trong trình soạn thảo văn bản (Text Editor)
| Nút vật lý trên TrimUI | Thao tác tương ứng |
| :--- | :--- |
| **D-pad / Analog Joystick** | Di chuyển con trỏ văn bản trong khung soạn thảo |
| **Nút X** | Chuyển đổi giữa chế độ Điều hướng (`[NAV]`) và Bàn phím ảo (`[OSK]`) |
| **Nút B** | Xóa ký tự (Delete) |
| **Nút Y** | Hoàn tác (Undo) |
| **Nút vai L1 / R1** | Chuyển đổi hoa / thường trên bàn phím ảo |
| **Nút SELECT** | Lưu thay đổi và đóng tệp (Save & Quit) |

---

## ⚙️ Hướng dẫn cài đặt

Để cài đặt ứng dụng lên máy TrimUI của bạn, chỉ cần làm theo các bước đơn giản sau:

1. Bấm vào nút `<> Code` màu xanh lá ở trên Github, sau đó chọn **Download ZIP** để tải mã nguồn về máy tính.
2. Giải nén file ZIP vừa tải ra, đảm bảo thư mục giải nén được đặt tên là `Files`.
3. **Copy toàn bộ thư mục `Files` đó và dán vào thư mục `Apps` nằm trên thẻ nhớ (SD Card) của máy.**
4. Lắp thẻ nhớ vào máy TrimUI, ứng dụng sẽ tự động xuất hiện trong giao diện menu Apps.

---

## 📜 Tuyên bố Mã nguồn mở (Open Source) & Bản quyền

Dự án này là mã nguồn mở và được phát hành dưới giấy phép **MIT License**. Bạn hoàn toàn có thể tự do sử dụng, học hỏi, sao chép hoặc phát triển thêm.

- **Tác giả gốc (Original Creator):** Nguyễn Ngọc Cường
- **Email liên hệ:** nn.cuong.404@gmail.com

Khi sử dụng lại hoặc tùy biến mã nguồn này, vui lòng giữ nguyên thông tin tác giả và bản quyền gốc theo quy định của giấy phép MIT đính kèm trong repository này.

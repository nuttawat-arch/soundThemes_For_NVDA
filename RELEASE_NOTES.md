# Sound Themes for NVDA 0.17.6

## What's new

- Rewrote all predefined sound Action descriptions in English and Thai, with accurate triggering conditions and practical examples. In the sound editor, select an Action to hear or read its explanation; no Action behavior was changed.
- Clarified Windows locking: `system.lock` is the first sound, while `system.lockscreen` is a second sound about 180 milliseconds later. Secure-desktop UAC events are separate.
- Clearly distinguished physical keyboard presses, text typing, navigation-focus sounds, key-release layers, and older compatibility slots that do not have automatic callbacks.
- Updated the Thai and English manuals and added description-focused regression tests. All sound assignments, WAV recordings, user preferences, sound-preservation behavior, and updater functionality remain unchanged.
- Automatic update checks stay at their existing unobtrusive schedule. GitHub Webhooks alone cannot push an update directly to NVDA without a separate public relay and client connection.

## มีอะไรใหม่

- เขียนคำอธิบาย Action ของเสียงทั้งหมดใหม่ทั้งภาษาไทยและอังกฤษ ให้ระบุเงื่อนไขการเล่นจริงและตัวอย่างการใช้งานอย่างชัดเจน เลือก Action ในหน้าแก้ไขเสียงเพื่อฟังหรืออ่านข้อความได้ โดย **ไม่เปลี่ยนวิธีทำงานของ Action**
- แยกความหมายของการล็อก Windows: `system.lock` เป็นเสียงแรก และ `system.lockscreen` เป็นเสียงที่สองหลังจากนั้นประมาณ 180 มิลลิวินาที ส่วนหน้าจอยืนยัน UAC เป็นอีเวนต์ต่างหาก
- อธิบายความต่างของเสียงกดคีย์บอร์ดจริง เสียงพิมพ์ข้อความ เสียงเลื่อนโฟกัส เสียงปล่อยปุ่ม และช่องเสียงรุ่นเก่าที่ยังไม่มีตัวเรียกอัตโนมัติ
- ปรับคู่มือไทยและอังกฤษ พร้อมเพิ่มการทดสอบ โดยยังคงไฟล์เสียง ค่าเสียงที่กำหนด การตั้งค่าผู้ใช้ การรักษาเสียงส่วนตัว และระบบอัปเดตเดิมทั้งหมด
- ยังใช้ระบบตรวจอัปเดตเบื้องหลังเดิม เพราะ GitHub Webhook อย่างเดียวไม่สามารถแจ้งเตือน NVDA ของผู้ใช้ได้ทันทีโดยไม่มีเซิร์ฟเวอร์รับและส่งต่อ

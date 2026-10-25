# Sound Themes for NVDA 0.17.4

## What's new

- Press **Space** while focused on an individual sound name to replay it at once. Space also replays a sample from the focused theme name; no need to move to the Preview button.
- Personal WAV edits survive a normal NVDA add-on update, **even if you modified a bundled preset directly instead of creating a copy**. Your audio remains inside the installed add-on; no separate active sound folder is created.
- The first upgrade from older releases conservatively keeps previous WAVs. Subsequent releases can recognize modified WAVs by checking the original bundled file hashes, preserving personal edits while untouched factory sounds receive updates. Custom packs, removed individual WAVs and unused edit backups are also preserved where they can be identified.
- Sound Themes now checks for new releases periodically while NVDA is running. A restart is not needed just to discover an update.
- Choose how often automatic checks run: every 10 or 30 minutes, every 1, 3, 6 or 12 hours, or daily. The default is every 30 minutes, and changes take effect when saved.
- When a new release becomes available, an accessible window shows the release notes in a read-only text field, with **Update now**, **Later** and **Skip this version** choices.
- A version is announced automatically only once, preventing interruptions at every check. Manual checks still show available releases.
- Update checks continue to run in the background without blocking typing or sound feedback. No add-on installs without your approval.
- Improved update status messages and distinct keyboard shortcuts for automatic checking (Alt+A) and checking now (Alt+U).

## มีอะไรใหม่

- **กด Space ที่ชื่อเสียงเพื่อฟังทันที** ไม่ต้องเลื่อนไปที่ปุ่มฟังตัวอย่าง และกด Space ที่ชื่อชุดเสียงเพื่อฟังเสียงตัวอย่างซ้ำได้เช่นกัน
- **อัปเดตแล้วเสียงส่วนตัวไม่หาย:** แม้แก้ไฟล์ WAV ในชุดเสียงมาตรฐานที่ติดตั้งมาโดยตรง โดยไม่ได้สร้างชุดใหม่ ระบบจะนำไฟล์ที่ปรับแต่งไว้ไปยังรุ่นใหม่ระหว่างขั้นตอนติดตั้งของ NVDA และยังเก็บเสียงไว้ในโฟลเดอร์ส่วนเสริม
- การอัปเดตครั้งแรกจากรุ่นเก่าจะรักษา WAV ที่มีอยู่ทั้งหมดก่อนเพื่อความปลอดภัย ส่วนรุ่นถัดไปจะใช้ค่าตรวจสอบไฟล์ต้นฉบับแยกเสียงที่แก้แล้วออกจากเสียงที่ไม่ได้แก้ ทำให้ไฟล์ส่วนตัวคงเดิมพร้อมรับการปรับปรุงของเสียงมาตรฐานที่ไม่ได้แก้ รวมทั้งเก็บชุดเสียงที่สร้างเองและไฟล์เสียงสำรองภายในชุด
- ตรวจหารุ่นใหม่เป็นระยะระหว่าง NVDA ทำงานได้ ไม่ต้องเริ่ม NVDA ใหม่เพียงเพื่อให้พบอัปเดต
- เลือกช่วงเวลาตรวจอัตโนมัติได้ ตั้งแต่ทุก 10 นาทีจนถึงทุก 24 ชั่วโมง โดยเริ่มต้นที่ทุก 30 นาที และมีผลทันทีหลังบันทึก
- เมื่อมีรุ่นใหม่ จะแสดงหน้าต่างรายการเปลี่ยนแปลงที่อ่านด้วย NVDA ได้ พร้อมตัวเลือก **อัปเดตตอนนี้**, **ไว้ภายหลัง** และ **ข้ามรุ่นนี้**
- แจ้งอัตโนมัติหนึ่งครั้งต่อรุ่น เพื่อไม่ให้รบกวนซ้ำทุกครั้งที่ตรวจ แต่ยังสั่งตรวจเองได้
- ตรวจข้อมูลผ่านเธรดเบื้องหลัง ไม่ขัดจังหวะการพิมพ์หรือเล่นเสียง และไม่ติดตั้งโดยพลการ
- ปรับข้อความสถานะและแยกปุ่มลัด Alt+A สำหรับตรวจอัตโนมัติ กับ Alt+U สำหรับตรวจทันที

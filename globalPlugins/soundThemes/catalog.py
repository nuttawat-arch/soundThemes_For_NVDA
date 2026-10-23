"""Public sound event vocabulary; independent from the NVDA runtime."""

from __future__ import annotations

import re


EVENT_GROUPS = {
    "System": {
        "system.start": "NVDA started", "system.stop": "NVDA stopping",
        "system.lock": "Windows session locked (first cue)",
        "system.lockscreen": "Windows lock screen (second cue)",
        "system.unlock": "Windows session unlocked",
        "system.secure_enter": "Secure desktop entered",
        "system.secure_exit": "Secure desktop left",
        "system.app_open": "Application opened / Explorer entered",
        "system.app_close": "Application closed / Explorer left",
        "system.app_switch": "Application switched",
        "system.window": "Foreground window", "system.alert": "Alert",
        "system.notification": "Notification", "system.media": "Media control",
        "system.error": "Error",
        "system.ready": "ScreenReaderSounds ready", "system.complete": "Document finished loading",
        "system.paused_feedback": "Speech feedback paused (when supported)",
        "system.tutorial": "Tutorial shortcut (when supported)",
        "system.volume_beep": "System volume feedback (when supported)",
    },
    "Keyboard": {
        "key.character": "Character typed", "key.space": "Space",
        "key.backspace": "Backspace / Delete", "key.protected": "Password character",
        "key.enter": "Enter / activation", "key.tab": "Tab / forward",
        "key.shift_tab": "Shift+Tab / backward", "key.up": "Up arrow",
        "key.down": "Down arrow", "key.left": "Left arrow",
        "key.right": "Right arrow", "key.page": "Page Up / Page Down",
        "key.home_end": "Home / End", "key.boundary": "Text boundary",
        "key.invalid": "Invalid navigation",
    },
    "Navigation": {
        "nav.focus": "Focus moved", "nav.browse": "Browse mode moved",
        "nav.quick": "Quick navigation", "nav.caret": "Caret moved",
        "nav.mouse": "Mouse hover", "nav.selection": "Selection changed",
        "nav.empty": "Unnamed / empty object", "nav.edit_exit": "Leaving edit/document",
        "nav.scroll": "Scrolled", "nav.open": "Item opened",
        "nav.close": "Item closed", "nav.expand": "Expanded",
        "nav.collapse": "Collapsed", "nav.activate": "Activated / clicked",
        "nav.long_activate": "Long press / long click (when supported)",
        "nav.tick": "Selection tick",
    },
    "NVDA states": {
        "state.off": "Switch turned off",
    },
    "Object events": {
        "object.foreground": "Foreground changed", "object.focus_entered": "Focus entered",
        "object.focus_lost": "Focus lost", "object.state": "State changed",
        "object.value": "Value changed", "object.name": "Name changed",
        "object.description": "Description changed",
        "object.show": "Object appeared", "object.hide": "Object disappeared",
        "object.document": "Document loaded", "object.text": "Text changed",
        "object.live": "Live region", "object.location": "Location changed",
    },
}

# Physical typing packs are deliberately isolated from navigation packs.
# Keys that move focus or the caret (Tab, arrows, Page Up/Down, Home/End)
# are navigation effects, not character typing effects.
TYPING_EVENTS = frozenset({
    "key.character", "key.space", "key.backspace", "key.protected", "key.enter",
})


# Explain the triggering NVDA event separately from the short, first-letter
# searchable list label. These strings never become part of a WAV filename.
# Do not promise application-specific hooks where none exist.
EVENT_DESCRIPTIONS = {
    "system.start": "When NVDA starts, regardless of the active application.",
    "system.stop": "When NVDA closes; the final sound before the screen reader exits.",
    "system.lock": "First sound on locking the Windows session with Win+L.",
    "system.lockscreen": "Second lock-screen sound shortly after Windows locks.",
    "system.unlock": "When the Windows session is unlocked again.",
    "system.secure_enter": "When NVDA enters the secure Windows desktop, such as a UAC prompt.",
    "system.secure_exit": "When NVDA returns from the secure desktop.",
    "system.app_open": "Legacy application-open cue. No separate reliable automatic trigger yet; assignable for future support.",
    "system.app_close": "Legacy application-close cue. No separate reliable automatic trigger yet; assignable for future support.",
    "system.app_switch": "When NVDA focus moves between different applications, for example Explorer and a browser.",
    "system.window": "When the foreground window changes in any application, including Windows dialogs.",
    "system.alert": "When an application sends NVDA an alert, such as a validation warning.",
    "system.notification": "When NVDA receives an application or Windows notification event.",
    "system.media": "Legacy media-control cue; automatic media-key detection is not reliable in every NVDA mode.",
    "system.error": "When NVDA requests its error sound; this is not every Windows error dialog.",
    "system.ready": "At NVDA startup when this event has a recording; otherwise the startup cue is used.",
    "system.complete": "When NVDA reports that a document finished loading, such as a page in a browser.",
    "system.paused_feedback": (
        "NVDA's speech-pause event, NOT the physical Shift key sound. "
        "Shift commonly pauses NVDA speech, so it used to trigger an unwanted second sound. "
        "Speech-pause feedback is off by default and Shift is always excluded; "
        "enable it separately in Sound Themes settings for other pause events."
    ),
    "system.tutorial": "Legacy tutorial-shortcut cue. No confirmed automatic trigger in current NVDA.",
    "system.volume_beep": "Legacy system-volume beep. No confirmed automatic trigger in current NVDA.",
    "key.character": "When a character is typed in a text field, editor or other typing control.",
    "key.space": "When a space character is entered in a text or editable field.",
    "key.backspace": "When a Backspace or Delete character is reported while editing text.",
    "key.protected": "When entering text in a password or other protected edit field.",
    "key.enter": "When an Enter/newline character is reported by an edit control, not every Enter keypress.",
    "key.tab": "Tab-related navigation context; plays only on a supported NVDA event, not every raw Tab press.",
    "key.shift_tab": "Reverse Tab navigation context; distinct from the physical Shift key sound.",
    "key.up": "Up-arrow navigation context when an NVDA focus or caret event is reported.",
    "key.down": "Down-arrow navigation context when an NVDA focus or caret event is reported.",
    "key.left": "Left-arrow navigation context when an NVDA focus or caret event is reported.",
    "key.right": "Right-arrow navigation context when an NVDA focus or caret event is reported.",
    "key.page": "When Page Up or Page Down causes NVDA to report movement or scrolling.",
    "key.home_end": "Home or End navigation context, for example moving to the edge of a text line.",
    "key.boundary": "Legacy cue for reaching a text boundary; automatic trigger is not guaranteed.",
    "key.invalid": "When invalid navigation is reported, for example an unsupported arrow action in a list.",
    "nav.focus": "Fallback when keyboard focus moves to an element without a more specific role sound.",
    "nav.browse": "When Browse Mode moves through web content or a document, for example in a browser.",
    "nav.quick": "Legacy quick-navigation cue; not every NVDA single-letter navigation command is detected.",
    "nav.caret": "When text caret movement follows navigation keys in an editor or document; not ordinary typing.",
    "nav.mouse": "When NVDA detects mouse hover over an object without a known role, if mouse sounds are enabled.",
    "nav.selection": "When NVDA reports a selection change without a specific list/tree item role sound.",
    "nav.empty": "When focus reaches an unnamed object with unknown NVDA role.",
    "nav.edit_exit": "When focus leaves an editable text control for another element.",
    "nav.scroll": "When Page Up or Page Down moves focus and NVDA reports it; this is not every mouse-wheel scroll.",
    "nav.open": "When focus switches into File Explorer from another app; also available as a legacy cue.",
    "nav.close": "When focus switches away from File Explorer to another app; also available as a legacy cue.",
    "nav.expand": "When NVDA reports that a tree node or expandable control expanded.",
    "nav.collapse": "When NVDA reports that a tree node or expandable control collapsed.",
    "nav.activate": "When NVDA reports activation, pressing or checking an actionable control.",
    "nav.long_activate": "Legacy long-press cue; there is no confirmed reliable automatic trigger in current NVDA.",
    "nav.tick": "A generic selection tick, such as choosing an option or item without a more specific role cue.",
    "state.off": "When NVDA reports a switch becoming off, such as a toggle in Settings.",
    "object.foreground": "When NVDA receives an event for the newly foregrounded window in any application.",
    "object.focus_entered": "When NVDA reports focus entering a group or container of controls.",
    "object.focus_lost": "When an NVDA object loses focus.",
    "object.state": "When an object's accessibility state changes without a more specific sound.",
    "object.value": "When a control's value changes, such as a slider, progress bar or text value.",
    "object.name": "When the accessible name of a control changes.",
    "object.description": "When an app changes an element's accessible description.",
    "object.show": "When an accessibility object becomes visible, such as a newly shown control.",
    "object.hide": "When an accessibility object disappears from the accessibility tree.",
    "object.document": "When NVDA reports completion of a document load, for example a browser page.",
    "object.text": "When an application's accessible text content changes.",
    "object.live": "When live-region content updates, often on dynamic websites in a browser.",
    "object.location": "When an element's position or size changes within its window.",
}

ROLE_CONTEXT = {
    "listitem": "File in File Explorer's file list, a message in an inbox, or an item in another list.",
    "treeviewitem": "Folder in File Explorer's navigation tree, or a nested item in another app.",
    "dataitem": "Item in a data grid, including Explorer's Details view or other application tables.",
    "button": "Button in Windows, a website or an application dialog.",
    "checkbox": "Checkbox in Settings, a form or another application.",
    "radiobutton": "Radio option within a group of choices.",
    "link": "Link in a browser, document or application.",
    "tab": "Tab in a browser or another application's tab bar.",
    "tabcontrol": "Tab container in a browser or application.",
    "menuitem": "Menu command in a Windows application or context menu.",
    "edit": "Text input field in a form or application.",
    "editabletext": "Editable text field in an editor, form or application.",
    "document": "Document area in a browser, editor or reader.",
    "tablecell": "Cell in a spreadsheet, website table or application grid.",
    "row": "Row in a table or details list, such as Explorer Details view.",
    "heading": "Heading within web content or a document.",
    "combobox": "Combo box for selecting options in an application form.",
    "list": "List containing items, such as files in File Explorer.",
    "treeview": "Tree containing folders or expandable branches.",
    "dialog": "Dialog opened by Windows or an application.",
    "progressbar": "Progress indicator for a task such as a download.",
    "slider": "Slider for volume or another numeric setting.",
}


# NVDA users running its Thai interface receive Thai explanations; event
# identifiers and list labels remain identical for all interface languages.
TH_EVENT_DESCRIPTIONS = {
    "system.start": "เสียงเมื่อ NVDA เริ่มทำงาน ไม่ว่าอยู่ในแอปใด",
    "system.stop": "เสียงขณะ NVDA กำลังปิดตัว",
    "system.lock": "เสียงแรกเมื่อกด Windows+L เพื่อล็อกหน้าจอ",
    "system.lockscreen": "เสียงที่สองหลัง Windows เข้าสู่หน้าจอล็อก",
    "system.unlock": "เสียงเมื่อปลดล็อก Windows กลับเข้าสู่ระบบ",
    "system.secure_enter": "เสียงเมื่อเข้าสู่หน้าจอปลอดภัย เช่น หน้าต่างยืนยันสิทธิ์ UAC",
    "system.secure_exit": "เสียงเมื่อออกจากหน้าจอปลอดภัย กลับสู่เดสก์ท็อปปกติ",
    "system.app_open": "เสียงเปิดแอปจากส่วนเสริมเดิม ปัจจุบันยังไม่มีอีเวนต์อัตโนมัติที่เชื่อถือได้",
    "system.app_close": "เสียงปิดแอปจากส่วนเสริมเดิม ปัจจุบันยังไม่มีอีเวนต์อัตโนมัติที่เชื่อถือได้",
    "system.app_switch": "เสียงเมื่อสลับโฟกัสระหว่างโปรแกรม เช่น จาก File Explorer ไปเบราว์เซอร์",
    "system.window": "เสียงเมื่อหน้าต่างด้านหน้าสุดเปลี่ยน เช่น เปิดกล่องโต้ตอบในโปรแกรม",
    "system.alert": "เสียงเมื่อแอปส่งข้อความเตือนให้ NVDA เช่น ข้อผิดพลาดในฟอร์ม",
    "system.notification": "เสียงเมื่อ NVDA ได้รับการแจ้งเตือนจากแอปหรือ Windows",
    "system.media": "เสียงปุ่มสื่อจากระบบเดิม ไม่รับประกันว่าจะตรวจพบทุกปุ่มหรือทุกโหมด",
    "system.error": "เสียงเมื่อ NVDA ขอเล่นเสียงแจ้งข้อผิดพลาด ไม่ใช่ทุกหน้าต่าง Error ของ Windows",
    "system.ready": "เสียงเมื่อ NVDA พร้อมใช้งานหลังเริ่มต้น หากไม่มีไฟล์จะใช้เสียงเริ่มต้นแทน",
    "system.complete": "เสียงเมื่อ NVDA แจ้งว่าโหลดเอกสารเสร็จ เช่น เว็บเพจในเบราว์เซอร์",
    "system.paused_feedback": (
        "เสียงตอน NVDA พักเสียงพูด ไม่ใช่เสียงกดปุ่ม Shift จริง การกด Shift มักสั่งพักเสียงพูดจึงเคยมีเสียงซ้อน "
        "รุ่นนี้ปิดเสียงอีเวนต์นี้เป็นค่าเริ่มต้น และไม่เล่นเสียงนี้จาก Shift แม้เปิดตัวเลือกไว้ "
        "สามารถเปิดเสียงพักเสียงพูดกรณีอื่นแยกได้ในหน้าตั้งค่า"
    ),
    "system.tutorial": "เสียงทางลัดสอนใช้จากส่วนเสริมเดิม ปัจจุบันยังไม่มีอีเวนต์อัตโนมัติที่ยืนยันได้",
    "system.volume_beep": "เสียงตอบรับปรับระดับเสียงจากระบบเดิม ปัจจุบันยังไม่มีอีเวนต์อัตโนมัติที่ยืนยันได้",
    "key.character": "เสียงเมื่อพิมพ์ตัวอักษรในช่องข้อความ โปรแกรมแก้ไขข้อความ หรือฟอร์ม",
    "key.space": "เสียงเมื่อป้อนช่องว่างในช่องแก้ไขข้อความ",
    "key.backspace": "เสียงเมื่อลบตัวอักษรด้วย Backspace หรือ Delete ขณะ NVDA รายงานการพิมพ์",
    "key.protected": "เสียงเมื่อพิมพ์ในช่องรหัสผ่านหรือช่องข้อความที่ซ่อนตัวอักษร",
    "key.enter": "เสียงเมื่อช่องแก้ไขข้อความรายงาน Enter หรือขึ้นบรรทัดใหม่ ไม่ใช่ทุกครั้งที่กดปุ่ม Enter",
    "key.tab": "เสียงบริบทการเลื่อนด้วย Tab เมื่อ NVDA มีอีเวนต์เกี่ยวข้อง ไม่ใช่เสียงกด Tab จริงทุกครั้ง",
    "key.shift_tab": "เสียงเลื่อนย้อนด้วย Shift+Tab ไม่ใช่เสียงปุ่ม Shift จริง",
    "key.up": "เสียงบริบทลูกศรขึ้น เมื่อมีการเปลี่ยนโฟกัสหรือตำแหน่งใน NVDA",
    "key.down": "เสียงบริบทลูกศรลง เมื่อมีการเปลี่ยนโฟกัสหรือตำแหน่งใน NVDA",
    "key.left": "เสียงบริบทลูกศรซ้าย เมื่อ NVDA รายงานการเคลื่อนตำแหน่ง",
    "key.right": "เสียงบริบทลูกศรขวา เมื่อ NVDA รายงานการเคลื่อนตำแหน่ง",
    "key.page": "เสียงเมื่อ Page Up หรือ Page Down ทำให้ NVDA รายงานการเลื่อนหน้า",
    "key.home_end": "เสียงบริบทการเลื่อนด้วย Home หรือ End เช่น ไปต้นหรือท้ายบรรทัด",
    "key.boundary": "เสียงถึงขอบข้อความจากระบบเดิม ยังไม่รับประกันว่าจะเล่นอัตโนมัติ",
    "key.invalid": "เสียงเมื่อเลื่อนไปตำแหน่งที่ไม่รองรับ เช่น กดลูกศรในรายการที่เลื่อนต่อไม่ได้",
    "nav.focus": "เสียงสำรองเมื่อโฟกัสย้ายไปส่วนควบคุมที่ไม่มีเสียงตามบทบาทเฉพาะ",
    "nav.browse": "เสียงเมื่อเลื่อนใน Browse Mode เช่น อ่านเว็บเพจหรือเอกสารในเบราว์เซอร์",
    "nav.quick": "เสียงเลื่อนด่วนจากระบบเดิม ยังตรวจจับคำสั่งเลื่อนอักษรตัวเดียวของ NVDA ไม่ครบทุกแบบ",
    "nav.caret": "เสียงเมื่อย้ายเคอร์เซอร์ข้อความด้วยปุ่มนำทางในเอกสารหรือโปรแกรมแก้ไข ไม่ใช่ตอนพิมพ์ทั่วไป",
    "nav.mouse": "เสียงเมื่อใช้เมาส์ชี้วัตถุที่ไม่ทราบบทบาท และเปิดเสียงเมาส์ไว้",
    "nav.selection": "เสียงเปลี่ยนการเลือก เมื่อไม่มีเสียงรายการหรือต้นไม้ที่เฉพาะเจาะจงกว่า",
    "nav.empty": "เสียงเมื่อย้ายโฟกัสไปยังวัตถุไม่ทราบชนิดและไม่มีชื่อ",
    "nav.edit_exit": "เสียงเมื่อออกจากช่องแก้ไขข้อความไปส่วนควบคุมชนิดอื่น",
    "nav.scroll": "เสียงเมื่อ Page Up หรือ Page Down ทำให้เกิดอีเวนต์เลื่อนที่ NVDA ตรวจพบ ไม่ใช่ทุกครั้งที่หมุนล้อเมาส์",
    "nav.open": "เสียงเมื่อสลับจากโปรแกรมอื่นเข้ามาที่ File Explorer",
    "nav.close": "เสียงเมื่อสลับออกจาก File Explorer ไปโปรแกรมอื่น",
    "nav.expand": "เสียงเมื่อรายการต้นไม้หรือส่วนควบคุมแบบขยายได้ถูกขยาย",
    "nav.collapse": "เสียงเมื่อรายการต้นไม้หรือส่วนควบคุมแบบขยายได้ถูกยุบ",
    "nav.activate": "เสียงเมื่อกดเปิดใช้งานปุ่ม ติ๊กตัวเลือก หรือเรียกคำสั่งจากส่วนควบคุม",
    "nav.long_activate": "เสียงกดค้างจากส่วนเสริมเดิม ยังไม่พบอีเวนต์อัตโนมัติที่เชื่อถือได้",
    "nav.tick": "เสียงติ๊กเลือกตัวเลือกหรือรายการที่ไม่มีเสียงบทบาทเฉพาะ",
    "state.off": "เสียงเมื่อสวิตช์หรือปุ่มสลับในแอปเปลี่ยนเป็นปิด",
    "object.foreground": "เสียงเมื่อ NVDA ได้รับอีเวนต์เปลี่ยนหน้าต่างด้านหน้าในแอปใดก็ได้",
    "object.focus_entered": "เสียงเมื่อโฟกัสเข้าไปในกลุ่มหรือพื้นที่รวมส่วนควบคุม",
    "object.focus_lost": "เสียงเมื่อวัตถุที่ NVDA ติดตามเสียโฟกัส",
    "object.state": "เสียงเมื่อสถานะการเข้าถึงของส่วนควบคุมเปลี่ยน โดยไม่มีเสียงอื่นที่เฉพาะเจาะจงกว่า",
    "object.value": "เสียงเมื่อค่าของส่วนควบคุมเปลี่ยน เช่น แถบเลื่อนหรือแถบความคืบหน้า",
    "object.name": "เสียงเมื่อชื่อที่โปรแกรมส่งให้โปรแกรมอ่านหน้าจอเปลี่ยน",
    "object.description": "เสียงเมื่อคำอธิบายสำหรับโปรแกรมอ่านหน้าจอของวัตถุเปลี่ยน",
    "object.show": "เสียงเมื่อส่วนควบคุมปรากฏขึ้นในโครงสร้างการเข้าถึง",
    "object.hide": "เสียงเมื่อส่วนควบคุมหายไปจากโครงสร้างการเข้าถึง",
    "object.document": "เสียงเมื่อ NVDA รายงานว่าเอกสารโหลดเสร็จ เช่น หน้าเว็บ",
    "object.text": "เสียงเมื่อข้อความที่โปรแกรมส่งให้ NVDA เปลี่ยน",
    "object.live": "เสียงเมื่อพื้นที่แจ้งข้อความสดเปลี่ยน เช่น ผลลัพธ์ที่เว็บอัปเดตโดยไม่โหลดหน้าใหม่",
    "object.location": "เสียงเมื่อตำแหน่งหรือขนาดวัตถุบนหน้าจอเปลี่ยน",
}

TH_ROLE_CONTEXT = {
    "listitem": "รายการไฟล์ใน File Explorer รายการอีเมล หรือรายการในแอปอื่น",
    "treeviewitem": "โฟลเดอร์ในแผงต้นไม้ด้านข้าง File Explorer หรือรายการย่อยในแอปอื่น",
    "dataitem": "รายการในตารางข้อมูล เช่น มุมมอง Details ของ File Explorer",
    "button": "ปุ่มในแอป Windows หน้าเว็บ หรือกล่องโต้ตอบ",
    "checkbox": "ช่องทำเครื่องหมายใน Settings หรือฟอร์ม",
    "radiobutton": "ตัวเลือกวงกลมในกลุ่มตัวเลือก",
    "link": "ลิงก์ในเบราว์เซอร์ เอกสาร หรือแอป",
    "tab": "แท็บของเบราว์เซอร์หรือโปรแกรมอื่น",
    "tabcontrol": "แถบแท็บรวมของเบราว์เซอร์หรือโปรแกรม",
    "menuitem": "คำสั่งในเมนูหรือเมนูคลิกขวาของโปรแกรม",
    "edit": "ช่องป้อนข้อความในฟอร์มหรือแอป",
    "editabletext": "ช่องแก้ไขข้อความในเอกสารหรือฟอร์ม",
    "document": "พื้นที่เอกสารในเบราว์เซอร์ โปรแกรมแก้ไข หรือโปรแกรมอ่าน",
    "tablecell": "เซลล์ในสเปรดชีต ตารางเว็บ หรือตารางข้อมูล",
    "row": "แถวในตาราง เช่น มุมมอง Details ของ Explorer",
    "heading": "หัวเรื่องในเว็บเพจหรือเอกสาร",
    "combobox": "ช่องเลือกรายการแบบเลื่อนลงในฟอร์ม",
    "list": "รายการ เช่น ไฟล์ใน File Explorer",
    "treeview": "ต้นไม้โฟลเดอร์หรือหมวดย่อยที่ขยายและยุบได้",
    "dialog": "หน้าต่างโต้ตอบของ Windows หรือโปรแกรม",
    "progressbar": "แถบแสดงความคืบหน้าของงาน เช่น การดาวน์โหลด",
    "slider": "แถบเลื่อนระดับเสียงหรือค่าอื่น",
}


def event_description(event_key: str, label: str = "", language: str = "en") -> str:
    """Human explanation of an event, without altering first-letter list search."""
    thai = language.lower().startswith("th")
    if thai and event_key in TH_EVENT_DESCRIPTIONS:
        return TH_EVENT_DESCRIPTIONS[event_key]
    if event_key in EVENT_DESCRIPTIONS:
        return EVENT_DESCRIPTIONS[event_key]
    display = label or event_key.rsplit(".", 1)[-1].replace("_", " ")
    if event_key.startswith("keyboard."):
        if thai:
            if event_key == "keyboard.default":
                return "เสียงสำรองภายในชุดคีย์บอร์ดนี้ เมื่อปุ่มจริงไม่มีไฟล์เสียงที่กำหนดแยก"
            if event_key in ("keyboard.shift", "keyboard.left_shift", "keyboard.right_shift"):
                return f"เสียงกดปุ่ม {display} จริง เมื่อเปิด Keyboard Sounds เท่านั้น ไม่ใช่เสียง NVDA พักเสียงพูด"
            if event_key in ("keyboard.fn", "keyboard.brightness_up", "keyboard.brightness_down"):
                return f"เสียงปุ่ม {display} หาก Windows ส่งเหตุการณ์ให้ NVDA ได้ โน้ตบุ๊กหลายรุ่นไม่ส่ง"
            return f"เสียงตอนกดปุ่ม {display} จริง ใน File Explorer เบราว์เซอร์ หรือแอปใดก็ได้ เมื่อเปิด Keyboard Sounds"
        if event_key == "keyboard.default":
            return "Fallback recording inside this keyboard pack when a physical key has no exact WAV."
        if event_key in ("keyboard.shift", "keyboard.left_shift", "keyboard.right_shift"):
            return (f"Physical {display} key-down in Keyboard Sounds mode only. "
                    "This is separate from NVDA's speech-pause event; one press should play only one key sound.")
        if event_key in ("keyboard.fn", "keyboard.brightness_up", "keyboard.brightness_down"):
            return f"Physical {display} if Windows and NVDA deliver that hardware key; many laptops do not."
        return (f"Physical {display} key-down while Keyboard Sounds mode is enabled, "
                "in Explorer, a browser or any app. Not triggered merely by moving NVDA focus.")
    if event_key == "role.default":
        if thai:
            return "เสียงสำรองเมื่อโฟกัสอยู่บนวัตถุชนิดที่ไม่มีไฟล์เสียงบทบาทตรงกับรายการนี้"
        return "Fallback when NVDA focus enters an object role that has no exact WAV in this theme."
    if event_key.startswith("role."):
        if thai:
            context = TH_ROLE_CONTEXT.get(event_key[5:], "ส่วนควบคุมชนิดนี้ในแอปใดก็ได้")
            return f"เสียงเมื่อโฟกัสย้ายไปยังบทบาท {display} ตัวอย่าง: {context}"
        context = ROLE_CONTEXT.get(event_key[5:], "A matching accessible control in any application.")
        return f"When NVDA focuses an object with role {display}. Example: {context}"
    if event_key == "state.default":
        if thai:
            return "เสียงสำรองสำหรับสถานะการเข้าถึงที่ไม่มีไฟล์เสียงตรงกับชนิดนั้นในชุดนี้"
        return "Fallback for an accessibility state without an exact recording in this theme."
    if event_key.startswith("state."):
        if thai:
            return f"เสียงเมื่อ NVDA รายงานว่าสถานะ {display} ของส่วนควบคุมเปลี่ยน เกิดจากข้อมูลการเข้าถึงของแอป ไม่ใช่ปุ่มใดปุ่มหนึ่ง"
        return (f"When NVDA reports state {display} for the focused object or a changed control. "
                "The event comes from the application's accessibility information, not from a particular key.")
    if thai:
        return f"เสียงอีเวนต์ {display} เมื่อ NVDA รายงาน ไม่จำกัดเฉพาะแอปใดแอปหนึ่ง"
    return f"Event {display} when reported by NVDA; this is not tied to one particular application."


def is_typing_event(event: str) -> bool:
    return event in TYPING_EVENTS


def is_keyboard_event(event: str) -> bool:
    return event.startswith("keyboard.")


def canonical_name(value: object) -> str:
    """Unify Enum role/state names across modern NVDA releases."""
    name = getattr(value, "name", str(value))
    return re.sub(r"[^a-z0-9]", "", name.lower())


def all_events(roles=(), states=()):
    """Sorted (group, key, accessible label) tuples; add every runtime Role/State."""
    entries = [(group, key, label) for group, group_events in EVENT_GROUPS.items()
               for key, label in group_events.items()]
    for role in roles:
        name = canonical_name(role)
        if name:
            entries.append(("NVDA roles", f"role.{name}", str(getattr(role, 'name', name))))
    for state in states:
        name = canonical_name(state)
        if name:
            entries.append(("NVDA states", f"state.{name}", str(getattr(state, 'name', name))))
    entries.append(("NVDA roles", "role.default", "Any other role (fallback)"))
    entries.append(("NVDA states", "state.default", "Any other state (fallback)"))
    return sorted(entries, key=lambda row: (row[0], row[2].casefold()))


LEGACY_EVENTS = {
    "tab": "key.tab", "shifttab": "key.shift_tab", "clicked": "nav.activate",
    "media": "system.media", "scroll": "nav.scroll",
    "typekey": "key.character", "typekeyspace": "key.space",
    "typekeypr": "key.protected", "typekeyremove": "key.backspace",
    "closed": "nav.close", "opened": "nav.open", "notext": "nav.empty",
    "collapsed": "nav.collapse", "expanded": "nav.expand",
    "eclose": "nav.edit_exit", "delete": "key.backspace",
    "lock": "system.lock", "lockscreen": "system.lockscreen",
    "unlockscreen": "system.unlock", "error": "key.invalid",
    "end": "key.home_end", "space": "key.space",
}


def legacy_event_for_filename(stem: str, role_names=(), state_names=()) -> str | None:
    """Map ScreenReaderSounds / navSounds WAV filenames to the new format."""
    key = canonical_name(stem)
    if key in LEGACY_EVENTS:
        return LEGACY_EVENTS[key]
    if key in {canonical_name(role) for role in role_names}:
        return f"role.{key}"
    if key in {canonical_name(state) for state in state_names}:
        return f"state.{key}"
    return None


def candidates(event_key: str) -> tuple[str, ...]:
    """Choose an exact binding first; then cover unknown future NVDA roles/states."""
    if event_key in ("key.space", "key.backspace", "key.enter", "key.protected"):
        # Most source typing themes ship a general key recording but not a
        # separate Enter/Space/Backspace take. Never borrow from another pack,
        # synthesize a sound or mask a genuine dedicated recording.
        return (event_key, "key.character")
    if event_key == "keyboard.shift_tab":
        return (event_key, "keyboard.tab", "keyboard.default")
    if event_key.startswith("keyboard.") and event_key != "keyboard.default":
        # A real recording from this same keyboard pack may serve keys the
        # source recording set does not cover (e.g. F13 or volume keys).
        return (event_key, "keyboard.default")
    if event_key.startswith("role."):
        return (event_key, "role.default", "nav.focus")
    if event_key.startswith("state."):
        return (event_key, "state.default", "object.state")
    return (event_key,)

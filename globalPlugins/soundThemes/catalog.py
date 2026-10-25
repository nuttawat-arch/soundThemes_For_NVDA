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
    "system.start": (
        "NVDA startup fallback. Plays after this add-on starts only when the selected system theme "
        "has no system.ready recording; it is not a Windows sign-in or application-launch sound."
    ),
    "system.stop": (
        "Plays while NVDA is shutting down or unloading this add-on. It is not played "
        "each time you close an application or an ordinary window."
    ),
    "system.lock": (
        "First of two Windows session-lock sounds, sent when NVDA receives the lock-state callback "
        "(for example after Windows+L). It describes the session lock, not a password-field event."
    ),
    "system.lockscreen": (
        "Second sound for the same Windows lock operation, scheduled about 180 milliseconds after "
        "system.lock. This is not a separate 'blocked screen' action or the secure UAC desktop; "
        "an unlock before the delay cancels this second cue."
    ),
    "system.unlock": (
        "Plays when NVDA receives the Windows session-unlocked callback after the user signs "
        "back in. It is separate from returning from a UAC secure desktop."
    ),
    "system.secure_enter": (
        "Plays on an NVDA secure-desktop entry notification, such as switching to the UAC "
        "confirmation desktop. It does not mean Windows has been locked with Windows+L."
    ),
    "system.secure_exit": (
        "Plays when NVDA reports leaving the secure desktop and returning to the regular "
        "desktop. It does not represent unlocking a locked Windows session."
    ),
    "system.app_open": (
        "Compatibility slot from older sound packs. Opening a program does not currently "
        "generate a dedicated automatic event here; entering File Explorer uses nav.open instead."
    ),
    "system.app_close": (
        "Compatibility slot from older sound packs. Closing a program does not currently "
        "generate a dedicated automatic event here; leaving File Explorer uses nav.close instead."
    ),
    "system.app_switch": (
        "Plays when keyboard focus changes between two recognized, non-Explorer applications "
        "after an earlier application was seen. Switching into or out of File Explorer "
        "has its own nav.open/nav.close sounds."
    ),
    "system.window": (
        "Plays whenever NVDA reports a new foreground window, including a dialog inside the "
        "same application. The same foreground event also provides object.foreground, so "
        "both recordings can sound if assigned."
    ),
    "system.alert": (
        "Plays when an application exposes an accessibility alert to NVDA, such as a "
        "validation message. It is not guaranteed for every visual warning or system error."
    ),
    "system.notification": (
        "Plays when NVDA receives an accessible notification event from Windows or an "
        "application. Notifications that the app does not report to NVDA cannot be detected."
    ),
    "system.media": (
        "Legacy media-control sound slot. There is no dedicated automatic media-action "
        "callback in this version; physical media keys use keyboard.* in Keyboard Sounds mode."
    ),
    "system.error": (
        "Plays when NVDA's error-sound extension point is invoked. This does not mean all "
        "Windows error messages or invalid form entries will automatically trigger it."
    ),
    "system.ready": (
        "Preferred sound after Sound Themes finishes starting within NVDA. If this recording "
        "is missing from the selected theme, system.start is used as the startup fallback."
    ),
    "system.complete": (
        "Plays when NVDA reports that a document finished loading, such as a browser page. "
        "That event also triggers object.document if a recording is assigned there."
    ),
    "system.paused_feedback": (
        "NVDA's speech-pause event, NOT the physical Shift key sound. "
        "Shift commonly pauses NVDA speech, so it used to trigger an unwanted second sound. "
        "Speech-pause feedback is off by default and Shift is always excluded; "
        "enable it separately in Sound Themes settings for other pause events."
    ),
    "system.tutorial": (
        "Legacy tutorial-shortcut recording from an older add-on. The current runtime does "
        "not provide a dedicated automatic shortcut event for this slot."
    ),
    "system.volume_beep": (
        "Legacy volume-feedback recording from an older add-on. This slot has no dedicated "
        "automatic Windows-volume event; use physical keyboard volume-key recordings if needed."
    ),
    "key.character": (
        "Typing sound when NVDA reports a character from an editable field, such as a text "
        "box or editor. It follows typed text, rather than every hardware key press."
    ),
    "key.space": (
        "Typing sound for Space in an editable field. The raw-key fallback covers editors "
        "that do not deliver a typed-character callback and avoids a second duplicate sound."
    ),
    "key.backspace": (
        "Typing sound for Backspace or Delete in an editable field, including the raw-key "
        "fallback when NVDA sends no character callback. Both keys share this action."
    ),
    "key.protected": (
        "Typing sound when a writable password or other protected field has focus. "
        "It replaces the normal character, Enter or deletion cue for supported protected typing."
    ),
    "key.enter": (
        "Typing sound when Enter is pressed in a writable text control or NVDA reports a "
        "newline there. Activating an ordinary button is a Navigation event, not this action."
    ),
    "key.tab": (
        "Legacy Tab navigation slot; the runtime observes Tab only as focus-movement "
        "context and does not play this key.* slot directly. The focused item's role sound "
        "plays instead; use keyboard.tab for each physical key press."
    ),
    "key.shift_tab": (
        "Legacy reverse-Tab navigation slot. Focus changes play the destination item's "
        "role sound; for a physical Shift+Tab recording use keyboard.shift_tab."
    ),
    "key.up": (
        "Legacy Up-arrow navigation slot, not a general key-down sound. Actual focus or "
        "caret changes play role.* or nav.caret; physical presses use keyboard.up."
    ),
    "key.down": (
        "Legacy Down-arrow navigation slot, not a general key-down sound. Actual focus or "
        "caret changes play role.* or nav.caret; physical presses use keyboard.down."
    ),
    "key.left": (
        "Legacy Left-arrow navigation slot, not a general key-down sound. Actual focus or "
        "caret changes play role.* or nav.caret; physical presses use keyboard.left."
    ),
    "key.right": (
        "Legacy Right-arrow navigation slot, not a general key-down sound. Actual focus or "
        "caret changes play role.* or nav.caret; physical presses use keyboard.right."
    ),
    "key.page": (
        "Page Up/Page Down context slot, not played directly by the current runtime. "
        "Page-key focus movement can trigger nav.scroll; physical keys use keyboard.pageup/pagedown."
    ),
    "key.home_end": (
        "Home/End context slot kept for older packs. Actual movement is described through "
        "focus or caret events; keyboard.home/end handles physical presses."
    ),
    "key.boundary": (
        "Legacy recording for reaching the beginning or end of text. No dedicated "
        "automatic text-boundary callback is currently connected to this slot."
    ),
    "key.invalid": (
        "Compatibility sound that can play if NVDA reports a typed character while an "
        "arrow key is held on a list or tree. It does not detect every unsuccessful "
        "navigation command or system error."
    ),
    "nav.focus": (
        "Fallback Navigation sound when an object has no usable role, or when a role "
        "has no dedicated recording and the selected theme supplies this fallback. "
        "Known roles normally use role.* sounds."
    ),
    "nav.browse": (
        "Legacy general Browse Mode movement slot. Current browser navigation normally "
        "plays the element's role.* sound or nav.caret; this slot is not a separate "
        "automatic sound for every virtual-cursor move."
    ),
    "nav.quick": (
        "Legacy quick-navigation slot. NVDA single-letter browsing commands now favor "
        "the destination element's role.* sound; this slot is not guaranteed to fire automatically."
    ),
    "nav.caret": (
        "Plays when a navigation key moves the text caret and arrow-navigation sounds "
        "are enabled. Also serves as the fallback when a browser Browse Mode movement "
        "has no identifiable element role; normal typing alone is suppressed."
    ),
    "nav.mouse": (
        "Plays after the configured mouse-hover delay, when mouse sounds are on and "
        "NVDA reports a hover object without a role. Known roles play their role.* "
        "recording instead; generic document/pane hovers are ignored."
    ),
    "nav.selection": (
        "Plays when an NVDA selection event involves no recognized list or tree item "
        "role, and this theme does not have nav.tick. A recognized item uses its role sound."
    ),
    "nav.empty": (
        "Plays if keyboard focus reaches an object with neither an accessible name "
        "nor a known role. It does not play for every blank line or empty text field."
    ),
    "nav.edit_exit": (
        "Plays when focus leaves an object whose previous role was editable text and "
        "moves to another kind of control. It does not imply that a file or editor closed."
    ),
    "nav.scroll": (
        "Plays when Page Up or Page Down is held as a focus-move event occurs. "
        "It is not a general mouse-wheel, touchpad or scrollbar movement detector."
    ),
    "nav.open": (
        "Plays when focus moves from a different application into Windows File Explorer. "
        "This is an application-transition cue, not every folder or document opening."
    ),
    "nav.close": (
        "Plays when focus moves from File Explorer into another application. It does "
        "not necessarily mean Explorer has closed or a folder has been deleted."
    ),
    "nav.expand": (
        "Plays when NVDA's state-change event reports an expanded item or control, "
        "such as an expanded tree branch. Merely moving focus onto it may use state.expanded."
    ),
    "nav.collapse": (
        "Plays when NVDA's state-change event reports a collapsed item or control. "
        "Focus on an already collapsed item may use state.collapsed instead."
    ),
    "nav.activate": (
        "Plays when NVDA reports a pressed or checked control, or when Space/Enter "
        "activates a supported button, checkbox, menu item or list item. "
        "Not every mouse click in every application reports this event."
    ),
    "nav.long_activate": (
        "Legacy long-press recording. No separate reliable long-click or long-keypress "
        "callback is connected in this version, so assigning it alone enables no new detector."
    ),
    "nav.tick": (
        "Preferred generic selection sound for events that are not a recognized "
        "list/tree item. If this recording is missing, nav.selection is used instead."
    ),
    "state.off": (
        "Plays on an NVDA switch state-change event when the accessible switch is off. "
        "It is distinct from a regular unchecked checkbox and from turning off Sound Themes."
    ),
    "object.foreground": (
        "Plays when NVDA receives a foreground-window event in any application. "
        "The same event can play system.window too; each slot is independently assignable."
    ),
    "object.focus_entered": (
        "Plays when NVDA reports focus entering a containing group, pane or other "
        "accessibility object. This is not the same as every ordinary focus movement."
    ),
    "object.focus_lost": (
        "Plays when NVDA reports that an accessibility object lost focus. "
        "Whether the event arrives depends on the application and accessibility provider."
    ),
    "object.state": (
        "Fallback for an NVDA object state-change event that is not handled as a "
        "switch on/off, expand/collapse, or pressed/checked activation."
    ),
    "object.value": (
        "Plays when NVDA reports that a control's accessible value changed, "
        "for example a volume slider or progress indicator; not on every repaint."
    ),
    "object.name": (
        "Plays when an application's accessibility information reports a change in "
        "an object's name, such as a button label. It is not a normal text-typing event."
    ),
    "object.description": (
        "Plays when an object's accessible description changes. This is metadata "
        "provided to NVDA by the application, not the visible text of every paragraph."
    ),
    "object.show": (
        "Plays on NVDA's object-show event when an accessible element appears. "
        "Some apps expose this when a new control or panel becomes visible."
    ),
    "object.hide": (
        "Plays on NVDA's object-hide event when an accessible element disappears. "
        "Closing a whole application does not necessarily report this event."
    ),
    "object.document": (
        "Plays when NVDA reports document-load completion, often after loading a "
        "browser page. That same event can also play system.complete."
    ),
    "object.text": (
        "Plays when NVDA reports changed accessible text content, for instance in a "
        "dynamically updated editor or control. It does not fire on every keypress."
    ),
    "object.live": (
        "Plays on an NVDA live-region change, often when a website updates a status "
        "or chat message without reloading. Only accessibility-reported updates count."
    ),
    "object.location": (
        "Plays when NVDA reports an object's on-screen position or size changing. "
        "It does not represent GPS location, map navigation or cursor movement."
    ),
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
    "system.start": (
        "เสียงสำรองตอนเริ่ม NVDA จะเล่นหลังส่วนเสริมเริ่มทำงานก็ต่อเมื่อชุดเสียงที่เลือกไม่มีไฟล์ "
        "system.ready ไม่ใช่เสียงตอนเข้าสู่ Windows หรือเปิดโปรแกรมอื่น"
    ),
    "system.stop": (
        "เสียงขณะ NVDA กำลังปิดหรือส่วนเสริมถูกยกเลิกการทำงาน "
        "ไม่ได้เล่นทุกครั้งที่ปิดหน้าต่างหรือโปรแกรมทั่วไป"
    ),
    "system.lock": (
        "เสียงแรกเมื่อ NVDA รับแจ้งว่าเซสชัน Windows ถูกล็อก เช่น หลังใช้ Windows+L "
        "เป็นเสียงของสถานะล็อกระบบ ไม่ใช่เสียงจากช่องกรอกรหัสผ่าน"
    ),
    "system.lockscreen": (
        "เสียงที่สองของการล็อก Windows ครั้งเดียวกัน กำหนดให้เล่นหลังเสียง system.lock ประมาณ 180 มิลลิวินาที "
        "ไม่ใช่ Action ปิดกั้นหน้าจอแยกต่างหาก และไม่ใช่หน้าจอ UAC "
        "หากปลดล็อกก่อนครบเวลา ระบบจะยกเลิกเสียงที่สอง"
    ),
    "system.unlock": (
        "เสียงเมื่อ NVDA ได้รับแจ้งว่าเซสชัน Windows ปลดล็อกและกลับมาใช้งานได้ "
        "คนละเหตุการณ์กับการออกจากหน้าจอยืนยันสิทธิ์ UAC"
    ),
    "system.secure_enter": (
        "เสียงเมื่อ NVDA ได้รับแจ้งว่าเข้าสู่ Secure Desktop เช่น หน้ายืนยันสิทธิ์ของ UAC "
        "ไม่ได้หมายถึงการล็อก Windows ด้วย Windows+L"
    ),
    "system.secure_exit": (
        "เสียงเมื่อ NVDA ได้รับแจ้งว่าออกจาก Secure Desktop กลับสู่เดสก์ท็อปปกติ "
        "ไม่ใช่เสียงปลดล็อกเซสชัน Windows"
    ),
    "system.app_open": (
        "ช่องเสียงเปิดโปรแกรมจากชุดเสียงรุ่นเก่า ปัจจุบันไม่ได้เชื่อมกับอีเวนต์เปิดโปรแกรมโดยตรง "
        "หากสลับเข้ามาใน File Explorer จะใช้ nav.open แทน"
    ),
    "system.app_close": (
        "ช่องเสียงปิดโปรแกรมจากชุดเสียงรุ่นเก่า ปัจจุบันไม่ได้เชื่อมกับอีเวนต์ปิดโปรแกรมโดยตรง "
        "หากสลับออกจาก File Explorer จะใช้ nav.close แทน"
    ),
    "system.app_switch": (
        "เสียงเมื่อโฟกัสย้ายระหว่างสองโปรแกรมที่ไม่ใช่ File Explorer หลังตรวจพบโปรแกรมก่อนหน้าแล้ว "
        "การสลับเข้าหรือออกจาก File Explorer ใช้ nav.open หรือ nav.close โดยเฉพาะ"
    ),
    "system.window": (
        "เสียงเมื่อ NVDA รายงานการเปลี่ยนหน้าต่างที่อยู่ด้านหน้า รวมถึงกล่องโต้ตอบในโปรแกรมเดิม "
        "อีเวนต์เดียวกันนี้เรียก object.foreground ด้วย จึงอาจได้ยินสองเสียงหากตั้งไว้ทั้งคู่"
    ),
    "system.alert": (
        "เสียงเมื่อโปรแกรมส่งอีเวนต์แจ้งเตือนด้านการเข้าถึงให้ NVDA เช่น ข้อความตรวจสอบฟอร์ม "
        "ไม่ได้ครอบคลุมทุกกล่องเตือนหรือทุกข้อผิดพลาดของ Windows"
    ),
    "system.notification": (
        "เสียงเมื่อ NVDA ได้รับอีเวนต์การแจ้งเตือนจาก Windows หรือโปรแกรม "
        "หากโปรแกรมไม่ส่งข้อมูลการแจ้งเตือนให้ NVDA ส่วนเสริมจะตรวจจับไม่ได้"
    ),
    "system.media": (
        "ช่องเสียงสั่งงานสื่อจากชุดเสียงเดิม รุ่นนี้ยังไม่มีตัวดักอีเวนต์สั่งงานสื่อสำหรับช่องนี้โดยตรง "
        "หากต้องการเสียงปุ่มสื่อจริงให้ใช้ keyboard.* ในโหมด Keyboard Sounds"
    ),
    "system.error": (
        "เสียงเมื่อ NVDA เรียกจุดเชื่อมต่อเสียงแจ้งข้อผิดพลาดของตัวเอง "
        "ไม่ใช่ทุกครั้งที่ Windows แสดง Error หรือกรอกข้อมูลฟอร์มไม่ถูกต้อง"
    ),
    "system.ready": (
        "เสียงหลักเมื่อ Sound Themes เริ่มพร้อมทำงานภายใน NVDA "
        "หากชุดเสียงที่เลือกไม่มีไฟล์นี้ จะใช้ system.start เป็นเสียงสำรองตอนเริ่มต้น"
    ),
    "system.complete": (
        "เสียงเมื่อ NVDA รายงานว่าโหลดเอกสารเสร็จ เช่น หน้าเว็บในเบราว์เซอร์ "
        "อีเวนต์เดียวกันนี้ยังเรียก object.document หากมีการกำหนดเสียงไว้"
    ),
    "system.paused_feedback": (
        "เสียงตอน NVDA พักเสียงพูด ไม่ใช่เสียงกดปุ่ม Shift จริง การกด Shift มักสั่งพักเสียงพูดจึงเคยมีเสียงซ้อน "
        "รุ่นนี้ปิดเสียงอีเวนต์นี้เป็นค่าเริ่มต้น และไม่เล่นเสียงนี้จาก Shift แม้เปิดตัวเลือกไว้ "
        "สามารถเปิดเสียงพักเสียงพูดกรณีอื่นแยกได้ในหน้าตั้งค่า"
    ),
    "system.tutorial": (
        "ช่องเสียงทางลัดแนะนำการใช้งานจากส่วนเสริมรุ่นเก่า "
        "รุ่นปัจจุบันยังไม่ได้เชื่อมตัวตรวจจับอีเวนต์ทางลัดชนิดนี้โดยเฉพาะ"
    ),
    "system.volume_beep": (
        "ช่องเสียงปรับระดับเสียงจากส่วนเสริมรุ่นเก่า ยังไม่มีอีเวนต์ตรวจระดับเสียง Windows สำหรับช่องนี้โดยตรง "
        "หากต้องการเสียงปุ่มเพิ่มหรือลดเสียงให้ใช้ชุด Keyboard Sounds"
    ),
    "key.character": (
        "เสียงพิมพ์อักขระเมื่อ NVDA รายงานการพิมพ์ในช่องที่แก้ไขได้ เช่น โปรแกรมพิมพ์ข้อความหรือฟอร์ม "
        "ไม่ได้เล่นตามปุ่มฮาร์ดแวร์ทุกปุ่ม"
    ),
    "key.space": (
        "เสียงพิมพ์ Space ในช่องแก้ไขข้อความ รองรับกรณีที่โปรแกรมไม่ส่งอีเวนต์อักขระ "
        "โดยใช้ข้อมูลการกดปุ่มจริงและป้องกันการเล่นเสียงซ้ำ"
    ),
    "key.backspace": (
        "เสียงลบข้อความด้วย Backspace หรือ Delete ในช่องที่พิมพ์ได้ "
        "ใช้ Action เดียวกันทั้งสองปุ่ม และรองรับโปรแกรมที่ไม่ส่งอีเวนต์การพิมพ์กลับมา"
    ),
    "key.protected": (
        "เสียงเมื่อพิมพ์ในช่องรหัสผ่านหรือช่องที่ซ่อนอักขระและแก้ไขได้ "
        "ใช้แทนเสียงตัวอักษร Enter หรือการลบตามปกติในกรณีที่รองรับ"
    ),
    "key.enter": (
        "เสียง Enter เมื่อกดในช่องข้อความที่แก้ไขได้ หรือ NVDA รายงานการขึ้นบรรทัดใหม่ "
        "การกดปุ่ม OK หรือสั่งงานปุ่มทั่วไปเป็นเสียง Navigation ไม่ใช่ Action นี้"
    ),
    "key.tab": (
        "ช่องเสียง Tab ที่เก็บไว้รองรับชุดเสียงเก่า ปัจจุบันตรวจปุ่ม Tab เพื่อระบุบริบทการเปลี่ยนโฟกัส "
        "แต่ไม่ได้เรียกเสียง key.tab โดยตรง การย้ายโฟกัสใช้เสียงชนิดวัตถุ; เสียงปุ่มจริงใช้ keyboard.tab"
    ),
    "key.shift_tab": (
        "ช่องเสียงย้อนกลับด้วย Shift+Tab จากชุดเสียงเก่า การเปลี่ยนโฟกัสใช้เสียงของวัตถุปลายทาง "
        "หากต้องการเสียงเมื่อกด Shift+Tab จริงให้กำหนด keyboard.shift_tab"
    ),
    "key.up": (
        "ช่องเสียงลูกศรขึ้นจากชุดเสียงเก่า ไม่ได้เล่นตรงทุกครั้งที่กด "
        "การย้ายโฟกัสหรือเคอร์เซอร์ใช้ role.* หรือ nav.caret; เสียงปุ่มจริงใช้ keyboard.up"
    ),
    "key.down": (
        "ช่องเสียงลูกศรลงจากชุดเสียงเก่า ไม่ได้เล่นตรงทุกครั้งที่กด "
        "การย้ายโฟกัสหรือเคอร์เซอร์ใช้ role.* หรือ nav.caret; เสียงปุ่มจริงใช้ keyboard.down"
    ),
    "key.left": (
        "ช่องเสียงลูกศรซ้ายจากชุดเสียงเก่า ไม่ได้เล่นตรงทุกครั้งที่กด "
        "การย้ายโฟกัสหรือเคอร์เซอร์ใช้ role.* หรือ nav.caret; เสียงปุ่มจริงใช้ keyboard.left"
    ),
    "key.right": (
        "ช่องเสียงลูกศรขวาจากชุดเสียงเก่า ไม่ได้เล่นตรงทุกครั้งที่กด "
        "การย้ายโฟกัสหรือเคอร์เซอร์ใช้ role.* หรือ nav.caret; เสียงปุ่มจริงใช้ keyboard.right"
    ),
    "key.page": (
        "ช่องเสียงบริบท Page Up/Page Down ยังไม่ได้เล่นจากการกดปุ่มโดยตรง "
        "หากกดแล้วโฟกัสย้ายอาจเรียก nav.scroll; เสียงปุ่มจริงใช้ keyboard.pageup หรือ keyboard.pagedown"
    ),
    "key.home_end": (
        "ช่องเสียงบริบท Home/End จากชุดเสียงเก่า การเลื่อนจริงใช้เสียงโฟกัสหรือเคอร์เซอร์ "
        "หากต้องการเสียงปุ่มกดจริงให้ใช้ keyboard.home หรือ keyboard.end"
    ),
    "key.boundary": (
        "ช่องเสียงเมื่อถึงขอบต้นหรือท้ายข้อความจากชุดเสียงเดิม "
        "ปัจจุบันไม่มีตัวตรวจจับขอบข้อความโดยเฉพาะสำหรับ Action นี้"
    ),
    "key.invalid": (
        "เสียงที่อาจเล่นเมื่อ NVDA รายงานการพิมพ์อักขระระหว่างกดลูกศรบนรายการหรือต้นไม้ "
        "ไม่ได้ตรวจพบทุกครั้งที่เลื่อนต่อไม่ได้ และไม่ใช่เสียงข้อผิดพลาดของระบบทั้งหมด"
    ),
    "nav.focus": (
        "เสียง Navigation สำรองเมื่อวัตถุไม่มีบทบาทที่ใช้ได้ หรือไม่มีไฟล์เสียงตรงกับบทบาทนั้น "
        "หากมีเสียง role.* ตรงชนิดวัตถุ จะให้เสียงนั้นทำงานเป็นหลัก"
    ),
    "nav.browse": (
        "ช่องเสียงเคลื่อนใน Browse Mode แบบเดิม การอ่านเว็บปัจจุบันมักเล่นเสียง role.* ตามชนิดวัตถุ "
        "หรือ nav.caret หากระบุบทบาทไม่ได้ ไม่ใช่เสียงที่เล่นแยกทุกครั้งที่ขยับเคอร์เซอร์เสมือน"
    ),
    "nav.quick": (
        "ช่องเสียงคำสั่งเลื่อนด่วนจากชุดเดิม การกดอักษรนำทางหนึ่งตัวใน NVDA "
        "ปัจจุบันให้ความสำคัญกับเสียง role.* ของวัตถุปลายทาง ไม่รับประกันว่า Action นี้จะเล่นอัตโนมัติ"
    ),
    "nav.caret": (
        "เสียงเมื่อปุ่มนำทางทำให้เคอร์เซอร์ข้อความขยับและเปิดเสียงลูกศรไว้ "
        "ใช้เป็นเสียงสำรองของ Browse Mode เมื่อไม่ทราบชนิดวัตถุด้วย "
        "การพิมพ์ตัวอักษรตามปกติจะไม่เรียกเสียงนี้ซ้ำ"
    ),
    "nav.mouse": (
        "เสียงเมื่อเปิดเสียงเมาส์แล้วชี้วัตถุที่ไม่ทราบบทบาทนานตามเวลาที่กำหนด "
        "หากทราบบทบาทจะใช้ role.* แทน และข้ามพื้นที่เอกสารหรือแผงทั่วไปบางชนิด"
    ),
    "nav.selection": (
        "เสียงเมื่อ NVDA แจ้งเปลี่ยนการเลือกซึ่งไม่ใช่รายการหรือต้นไม้ที่รู้จัก "
        "และชุดเสียงไม่มี nav.tick หากเป็นรายการที่รู้จักจะใช้เสียงตามบทบาทแทน"
    ),
    "nav.empty": (
        "เสียงเมื่อโฟกัสไปยังวัตถุที่ไม่มีทั้งชื่อสำหรับโปรแกรมอ่านหน้าจอและบทบาทที่ทราบ "
        "ไม่ใช่เสียงช่องข้อความว่างหรือบรรทัดว่างทุกกรณี"
    ),
    "nav.edit_exit": (
        "เสียงเมื่อโฟกัสย้ายออกจากวัตถุที่มีบทบาทเป็นช่องแก้ไขข้อความไปยังส่วนควบคุมประเภทอื่น "
        "ไม่ได้หมายถึงการปิดไฟล์หรือปิดโปรแกรมแก้ไข"
    ),
    "nav.scroll": (
        "เสียงเมื่อกด Page Up หรือ Page Down ค้างอยู่ขณะที่ NVDA รับอีเวนต์ย้ายโฟกัส "
        "ไม่ใช่ตัวตรวจจับการหมุนล้อเมาส์ ทัชแพด หรือแถบเลื่อนทั้งหมด"
    ),
    "nav.open": (
        "เสียงเมื่อโฟกัสสลับจากโปรแกรมอื่นเข้ามายัง Windows File Explorer "
        "ไม่ได้เล่นทุกครั้งที่เปิดโฟลเดอร์หรือเอกสารภายใน Explorer"
    ),
    "nav.close": (
        "เสียงเมื่อโฟกัสสลับจาก File Explorer ไปโปรแกรมอื่น "
        "ไม่จำเป็นต้องหมายความว่า Explorer ปิดตัวหรือมีการลบโฟลเดอร์"
    ),
    "nav.expand": (
        "เสียงเมื่อ NVDA รายงานว่ารายการต้นไม้หรือส่วนควบคุมถูกขยายผ่านอีเวนต์เปลี่ยนสถานะ "
        "หากเพียงย้ายโฟกัสไปยังรายการที่ขยายอยู่แล้ว อาจใช้ state.expanded"
    ),
    "nav.collapse": (
        "เสียงเมื่อ NVDA รายงานว่ารายการต้นไม้หรือส่วนควบคุมถูกยุบผ่านอีเวนต์เปลี่ยนสถานะ "
        "หากเพียงย้ายโฟกัสไปยังรายการที่ยุบอยู่แล้ว อาจใช้ state.collapsed"
    ),
    "nav.activate": (
        "เสียงเมื่อ NVDA รายงานส่วนควบคุมเป็นสถานะกดหรือติ๊กเลือก "
        "หรือใช้ Space/Enter กับปุ่ม ช่องทำเครื่องหมาย เมนู หรือรายการที่รองรับ "
        "ไม่ได้ตรวจจับการคลิกทุกครั้งจากทุกโปรแกรม"
    ),
    "nav.long_activate": (
        "ช่องเสียงกดค้างจากส่วนเสริมรุ่นเก่า ปัจจุบันไม่มีตัวดักการกดค้างหรือคลิกค้าง "
        "ที่ทำงานได้อย่างน่าเชื่อถือสำหรับ Action นี้"
    ),
    "nav.tick": (
        "เสียงเลือกทั่วไปเมื่อ NVDA แจ้งการเลือกที่ไม่ได้เป็นรายการหรือต้นไม้ที่รู้จัก "
        "หากไม่มีไฟล์เสียงนี้จะใช้ nav.selection เป็นเสียงสำรอง"
    ),
    "state.off": (
        "เสียงเมื่อ NVDA รายงานว่าสวิตช์ของส่วนควบคุมเปลี่ยนเป็นปิด "
        "ต่างจากช่องทำเครื่องหมายทั่วไปและไม่เกี่ยวกับการปิดการทำงานของ Sound Themes"
    ),
    "object.foreground": (
        "เสียงเมื่อ NVDA ได้รับอีเวนต์ว่าหน้าต่างใดขึ้นมาอยู่ด้านหน้า "
        "อีเวนต์เดียวกันอาจเล่น system.window ด้วย สามารถกำหนดเสียงให้ทั้งสองช่องแยกกันได้"
    ),
    "object.focus_entered": (
        "เสียงเมื่อ NVDA แจ้งว่าโฟกัสเข้าสู่กลุ่ม พื้นที่ หรือวัตถุที่ครอบส่วนควบคุมหลายตัว "
        "ไม่ใช่ทุกครั้งที่เลื่อนจากปุ่มหนึ่งไปยังอีกปุ่มหนึ่ง"
    ),
    "object.focus_lost": (
        "เสียงเมื่อ NVDA ได้รับแจ้งว่าวัตถุหนึ่งสูญเสียโฟกัส "
        "จะเกิดขึ้นได้หรือไม่ขึ้นกับข้อมูลการเข้าถึงที่โปรแกรมส่งมา"
    ),
    "object.state": (
        "เสียงสำรองเมื่อ NVDA แจ้งสถานะของวัตถุเปลี่ยน และไม่ได้จัดเข้าเหตุการณ์สวิตช์เปิดปิด "
        "ขยาย ยุบ กด หรือเลือก ที่มีเสียงเฉพาะอยู่แล้ว"
    ),
    "object.value": (
        "เสียงเมื่อ NVDA ได้รับแจ้งว่าค่าของส่วนควบคุมเปลี่ยน เช่น ระดับเสียงบน Slider "
        "หรือเปอร์เซ็นต์ของแถบความคืบหน้า ไม่ใช่ทุกครั้งที่หน้าจอวาดใหม่"
    ),
    "object.name": (
        "เสียงเมื่อโปรแกรมเปลี่ยนชื่อที่ส่วนควบคุมประกาศให้โปรแกรมอ่านหน้าจอ เช่น ป้ายชื่อบนปุ่ม "
        "ไม่ใช่เสียงพิมพ์ตัวอักษรตามปกติ"
    ),
    "object.description": (
        "เสียงเมื่อคำอธิบายการเข้าถึงของวัตถุเปลี่ยน "
        "เป็นข้อมูลที่แอปส่งให้ NVDA ไม่ใช่ข้อความทุกย่อหน้าที่มองเห็นบนจอ"
    ),
    "object.show": (
        "เสียงเมื่อ NVDA ได้รับอีเวนต์ว่าวัตถุด้านการเข้าถึงปรากฏขึ้น "
        "เช่น โปรแกรมเพิ่มปุ่มหรือแผงใหม่ที่มองเห็นได้"
    ),
    "object.hide": (
        "เสียงเมื่อ NVDA ได้รับอีเวนต์ว่าวัตถุด้านการเข้าถึงหายไป "
        "การปิดโปรแกรมหนึ่งโปรแกรมไม่จำเป็นต้องสร้างอีเวนต์นี้ทุกครั้ง"
    ),
    "object.document": (
        "เสียงเมื่อ NVDA รายงานว่าเอกสารโหลดเสร็จ เช่น หน้าเว็บในเบราว์เซอร์ "
        "อีเวนต์เดียวกันอาจเล่น system.complete อีกเสียงหนึ่งด้วย"
    ),
    "object.text": (
        "เสียงเมื่อ NVDA แจ้งว่าข้อความที่วัตถุส่งให้โปรแกรมอ่านหน้าจอเปลี่ยน "
        "เช่น ข้อความที่โปรแกรมปรับปรุงอัตโนมัติ ไม่ใช่ทุกครั้งที่กดพิมพ์"
    ),
    "object.live": (
        "เสียงเมื่อ NVDA ได้รับอีเวนต์จาก Live Region เช่น เว็บอัปเดตสถานะหรือข้อความแชตโดยไม่โหลดใหม่ "
        "จะตรวจพบเฉพาะการเปลี่ยนที่เว็บส่งข้อมูลการเข้าถึงมาให้"
    ),
    "object.location": (
        "เสียงเมื่อ NVDA แจ้งว่าตำแหน่งหรือขนาดของวัตถุบนหน้าจอเปลี่ยน "
        "ไม่ใช่ตำแหน่ง GPS แผนที่ หรือการเลื่อนเคอร์เซอร์ข้อความ"
    ),
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
        # The editor exposes a press recording and optionally a distinct
        # release recording for that same key. Other callers may request a
        # .release description directly; do not describe key-up as key-down.
        release = event_key.endswith(".release")
        physical_event = event_key[:-8] if release else event_key
        key_name = display.removesuffix(".release").replace("_", " ")
        if thai:
            if physical_event == "keyboard.default":
                if release:
                    return ("เสียงสำรองตอนปล่อยปุ่มในชุดคีย์บอร์ดนี้ ใช้เฉพาะโหมดเสียงกดและปล่อยแยกกัน "
                            "เมื่อปุ่มนั้นไม่มีไฟล์ .release ของตัวเอง โดยไม่เอาเสียงกดมาเล่นแทน")
                return ("เสียงสำรองสำหรับปุ่มคีย์บอร์ดที่ไม่มีไฟล์กดของตัวเองภายในชุดนี้ "
                        "ใช้เฉพาะเมื่อเปิด Keyboard Sounds ไม่สุ่มเสียงจากชุดอื่น")
            if release:
                return (f"เสียงขณะปล่อยปุ่ม {key_name} จริง จะเล่นเฉพาะเมื่อเปิด Keyboard Sounds "
                        "และเลือกโหมดเสียงกดกับปล่อยแยกกัน โดยต้องมีไฟล์ปล่อยของปุ่มนี้หรือไฟล์สำรอง "
                        "ไม่ใช้เสียงกดแทนเสียงปล่อย")
            if physical_event in ("keyboard.shift", "keyboard.left_shift", "keyboard.right_shift"):
                return (f"เสียงกดปุ่ม {key_name} จริง เมื่อเปิด Keyboard Sounds โดยหนึ่งครั้งควรเล่นหนึ่งเสียง "
                        "แยกจากอีเวนต์ NVDA พักเสียงพูด และไม่ใช่เสียงเมื่อย้ายโฟกัส")
            if physical_event in ("keyboard.fn", "keyboard.brightness_up", "keyboard.brightness_down"):
                return (f"เสียงเมื่อกดปุ่ม {key_name} จริงในโหมด Keyboard Sounds เฉพาะกรณีที่ "
                        "Windows ส่งเหตุการณ์ปุ่มให้ NVDA ได้ โน้ตบุ๊กหลายรุ่นไม่ส่งปุ่มชนิดนี้")
            if physical_event.startswith("keyboard.mouse_"):
                return (f"เสียงปุ่ม {key_name} เมื่อ Windows และ NVDA ส่งเหตุการณ์ปุ่มนี้เข้าทางตัวดักคีย์บอร์ด "
                        "ไม่ใช่เสียงเมาส์ชี้วัตถุของ Navigation และอาจไม่รองรับในอุปกรณ์ทุกชนิด")
            return (f"เสียงเมื่อกดปุ่ม {key_name} จริงใน File Explorer เบราว์เซอร์ หรือโปรแกรมอื่น "
                    "เฉพาะเมื่อเปิด Keyboard Sounds ใช้ข้อมูลปุ่มจาก Windows ไม่ใช่อีเวนต์ย้ายโฟกัสของ NVDA "
                    "โหมดเสียงไฟล์เดียวสามารถบันทึกเสียงกดและปล่อยไว้ในไฟล์เดียวได้")
        if physical_event == "keyboard.default":
            if release:
                return ("Fallback key-release recording for this keyboard pack in separate-layer mode "
                        "when the key has no exact .release WAV. A key-down sample is never substituted.")
            return ("Fallback physical key-down recording when a key lacks an exact WAV in "
                    "this same keyboard pack. It does not randomly borrow another theme's sound.")
        if release:
            return (f"Physical {key_name} key-up in Keyboard Sounds' separate press/release mode only. "
                    "It requires an exact .release WAV or the pack's release fallback; "
                    "it is not played in combined single-file mode.")
        if physical_event in ("keyboard.shift", "keyboard.left_shift", "keyboard.right_shift"):
            return (f"Physical {key_name} key-down in Keyboard Sounds mode. "
                    "This is separate from NVDA speech pause, not a focus-change cue; "
                    "duplicate hardware modifier aliases are filtered.")
        if physical_event in ("keyboard.fn", "keyboard.brightness_up", "keyboard.brightness_down"):
            return (f"Physical {key_name} key-down, but only if Windows exposes that "
                    "hardware event to NVDA. Many laptop Fn/brightness keys are not delivered.")
        if physical_event.startswith("keyboard.mouse_"):
            return (f"Physical {key_name} if Windows/NVDA deliver it through the keyboard "
                    "hook; this is not Navigation mouse-hover feedback and may be unavailable.")
        return (f"Physical {key_name} key-down in Keyboard Sounds mode, in Explorer, a browser "
                "or another app, not simply when NVDA focus moves. In combined mode the "
                "single WAV may already contain both press and release sounds.")
    if event_key == "role.default":
        if thai:
            return ("เสียงสำรองเมื่อ NVDA พบวัตถุที่มีบทบาทแต่ชุดเสียงนี้ไม่มีไฟล์ role.* ตรงชนิดนั้น "
                    "อาจเกิดจากการเลื่อนโฟกัส รายการ หรือ Browse Mode; หากไม่มีเสียงสำรองนี้จะพิจารณา nav.focus")
        return ("Fallback when NVDA finds an object role without an exact role.* WAV "
                "in this theme, during focus or Browse Mode movement. If this recording is "
                "also missing, nav.focus may be used.")
    if event_key.startswith("role."):
        if thai:
            context = TH_ROLE_CONTEXT.get(event_key[5:], "ส่วนควบคุมชนิดนี้ในแอปใดก็ได้")
            return (f"เสียงเมื่อ NVDA ย้ายโฟกัส เลือกรายการ หรือเลื่อนเคอร์เซอร์ Browse Mode "
                    f"ไปยังวัตถุบทบาท {display} ตัวอย่าง: {context} "
                    "หากมีเสียงสถานะที่กำหนดตรงตัวและมีลำดับความสำคัญสูงกว่าอาจเล่นเสียงสถานะแทน "
                    "ไม่ใช่เสียงปุ่มที่ใช้เลื่อน")
        context = ROLE_CONTEXT.get(event_key[5:], "A matching accessible control in any application.")
        return (f"When NVDA focus, a recognized item selection or the Browse Mode cursor "
                f"reaches role {display}. Example: {context} "
                "A specifically assigned higher-priority state sound can override the role; "
                "this is not a physical navigation-key sound.")
    if event_key == "state.default":
        if thai:
            return ("เสียงสำรองสำหรับสถานะของวัตถุที่ไม่มีไฟล์ state.* ตรงชนิดนั้นในชุดเสียง "
                    "ใช้เมื่อระบบเลือกเสียงสถานะดังกล่าวแล้วเท่านั้น ไม่ใช่การแจ้งทุกสถานะของทุกวัตถุ")
        return ("Fallback when the engine requests a state sound that lacks an exact "
                "state.* WAV in this theme. It does not announce every state of every object.")
    if event_key.startswith("state."):
        if thai:
            return (f"เสียงสถานะ {display} จากข้อมูลการเข้าถึงของวัตถุที่ NVDA รายงาน "
                    "บางสถานะที่กำหนดเสียงไว้จะมีสิทธิ์เล่นแทนเสียง role.* ตอนโฟกัส "
                    "ส่วนสวิตช์เปิดปิดมีอีเวนต์เปลี่ยนสถานะเฉพาะ ไม่ได้หมายถึงทุกสถานะจะเล่นทุกครั้งที่เปลี่ยน")
        return (f"Accessible state {display}, reported by NVDA. Certain explicitly assigned "
                "priority states can override a role sound on focus; switch on/off has its "
                "own change callback. Not every state change fires this sound automatically.")
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
    "longclicked": "nav.long_activate", "complete": "system.complete",
    "italic": "state.italic", "pausedfeedback": "system.paused_feedback",
    "tutorialtrigger": "system.tutorial", "ready": "system.ready",
    "tick": "nav.tick", "volumebeep": "system.volume_beep",
    "edetabletext": "role.editabletext", "hedingh": "role.heading",
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
    if event_key.startswith("keyboard.") and event_key.endswith(".release"):
        # Release must never borrow a press recording: that produces an
        # unexpected second click in packs without key-up samples.
        if event_key == "keyboard.shift_tab.release":
            return (event_key, "keyboard.tab.release", "keyboard.default.release")
        return (event_key, "keyboard.default.release")
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

# Read LectureLive captions on your phone

Available in **0.8.0b1 and later**. Students need a phone browser and a connection to the lecturer’s local network. No account, app installation, mobile data or internet service is needed during the lecture. The lecturer’s computer still runs all speech recognition and translation.

## Lecturer: share a lecture

1. Open LectureLive. Keep your usual microphone, speaking language and recognition settings.
2. Connect your computer and the students’ phones to the **same trusted Wi-Fi network**. An Ethernet-connected lecturer computer also works if the network permits phones to reach it.
3. Open **Student phones**. Choose the Wi-Fi or Ethernet address from the list. Ignore VPN and virtual-machine adapters. Use **Refresh networks** after connecting to Wi-Fi.
4. Click **Start sharing**. A QR code and private classroom link appear. Show the code to students, or use **Copy link** to distribute it yourself. **Open student view** lets you preview it.
5. Start the lecture normally. Speak in English, or use the existing Mandarin/manual/Auto controls. Completed recognised speech appears first; its translation fills the same entry when ready.
6. At the end, stop the lecture and give students time to download. Click **Stop sharing** to close the link and remove its temporary text history. Closing LectureLive also stops sharing.

Sharing always starts **off**, is not saved in a preset, and requires a new link for a new lecture. The projector continues to show the existing current-caption layout. Sharing has no microphone or language controls for students.

**Starting halfway through:** when normal transcript saving is on, sharing imports earlier entries from the current lecture’s journal. When normal saving is off, only entries captured while sharing is enabled are available. A coverage message in the reader explains which applies. Enable sharing before speaking to include the whole lecture.

## Student: follow and save

1. Connect to the same Wi-Fi, scan the QR code with your phone camera and open the link in your normal browser. Keep the full link, including its final slash.
2. Choose **English + 简体中文**, **English only**, or **仅简体中文**. Each entry labels the spoken language and the translation. Use **A− / A+** to change the text size.
3. New captions follow automatically while you are at the latest text. Scroll up to read earlier explanations: your reading position stays put when new captions or delayed translations arrive. Tap **Back to live / 返回实时** to catch up.
4. Open **Search, copy & download / 搜索与保存** to search the whole shared lecture, including older entries. Scroll or use the earlier/later buttons to page through results. Back to live clears the search.
5. Use an entry’s **Copy** button to copy that entry, or **Copy visible text** for the currently loaded group. This group is at most 120 entries; use the download for the whole lecture. If browser clipboard permission is blocked, select and copy text manually.
6. Tap **Download full .txt** to save all entries shared so far in your selected language view. This downloads the whole shared lecture, even while a search is active. Choose the bilingual view to save both languages. Find the file in your browser’s Downloads or Files app.

For example: the lecturer asks “What is the critical path?” in English. Its Chinese translation joins that entry. A student asks “请再解释一次。” in Mandarin; the recognised Chinese and English translation occupy the next entry. A slow translation updates its original entry rather than appearing later as a new turn.

Late arrivals see the latest captions and can scroll/search back through the available history. Refresh opens the latest text and preserves font/language preferences. After a brief connection loss, received text stays visible and the page retries automatically. Older text and downloads need a working connection. If the lecturer starts a new sharing session, scan the new code.

## Missing text or connection problems

- **The projector replaced an earlier paragraph:** that is normal for its current-caption layout. Read older completed entries on the phone or in saved transcripts. The projector can also clip an exceptionally long current caption to the available screen area.
- **Translation pending:** the recognised words are available but translation has not finished. Wait for that entry to update. A download taken now contains the pending marker; download again after translation finishes.
- **Translation unavailable / Audio lost / Not transcribed:** the app could not supply that content. Ask the speaker to repeat or clarify. Neither the reader nor saved files recover uncaptured audio or invent missing translations.
- **Phone cannot open the link:** check both devices’ network and the selected adapter. Guest/university Wi-Fi may isolate devices even when the network name matches. Ask IT to allow local connections to LectureLive; do not disable the firewall. If permitted, a private hotspot can provide a local network without internet.
- **Windows/macOS asks for incoming network permission:** allow LectureLive only on the trusted network under your organisation’s policy. Source builds may identify the helper as Python. Managed firewalls may require IT approval; the app does not change firewall rules.
- **Reconnecting:** keep the lecturer computer awake, check Wi-Fi, and confirm sharing is still on. A changed IP address requires stopping/restarting sharing and a new QR code. Try the link in Safari/Chrome/Edge if a camera’s embedded browser fails. Do not change an `http://` link to `https://`.
- **Phone sharing stopped with a history warning:** normal local captions and transcript saving continue. Save the normal transcript, correct the disk/load problem, then start sharing again. With normal saving enabled, the new session can import earlier text. Share the new QR code.

## Privacy, limits and classroom rehearsal

The link is private to the session, but anyone who has it and can reach the computer can read and download the shared text. Local HTTP is **not encrypted**. Use a trusted classroom network, avoid posting the code publicly, and follow university policy for sharing lecture/student contributions. Sharing creates temporary text storage even when normal transcript saving is off; it never records microphone audio. Stop removes the temporary history on a normal shutdown. An application/OS crash can leave a `phone-sharing/lecture-*` folder in LectureLive’s data directory; remove that folder after the app is closed if needed. Normal saved transcripts are separate. Stopping sharing cannot remove received text or downloaded copies from students’ devices.

Pause stops new listening but keeps earlier text available. Already queued translations can still finish and appear. Use **Stop sharing**, not Pause, to revoke the link. Ending a lecture leaves its shared history readable until you stop sharing or start a new lecture.

History is stored on disk, with small paged reads and at most 120 entries in the browser. No completed entries are silently evicted. The separate writer queue is bounded to 256 events / approximately 4 MiB; temporary history has a 512 MiB disk safety limit. A caption field over 128 Ki characters or a storage/queue limit stops sharing visibly rather than truncating text. These are safeguards, not claimed lecture-duration guarantees. Keep normal transcript saving enabled for recovery. Downloaded snapshots include completed entries and honest pending/failure notices at the time of download.

The reader polls about every 1.5 seconds, adding up to that interval plus local network time after a caption is available. It uses existing models, with **no extra model downloads or inference RAM requirement**. The helper, disk cache and phone browser do add modest resources; actual performance depends on the computer and classroom network. Private IPv4 networks are supported; IPv6-only networks are not supported in this beta. The helper caps concurrent active requests at 32; this is not a certified class-size limit.

Before teaching, try two physical phones on the intended Wi-Fi. Speak a long English paragraph, ask a Mandarin question, scroll back while the lecturer continues, switch the three views, search an early term, briefly toggle a phone’s Wi-Fi, and download the bilingual TXT. Compare with the lecturer’s saved transcript. Confirm Stop sharing prevents a fresh page load. Test a longer session with your expected student count. Automated mobile emulation and loopback load tests do not replace this rehearsal; see [test evidence](evidence/phone-captions-0.8.md).

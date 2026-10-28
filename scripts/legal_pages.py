"""Privacy, terms, and contact HTML. Vietnamese and English. No personal contact details."""


def _google_section(lang):
    if lang == "vi":
        return """<h2 id="quang-cao-google">Google AdSense</h2>
<p>Khi AdSense được bật, Google và các đối tác của Google có thể đặt cookie hoặc dùng mã nhận dạng trên thiết bị của bạn để đo lường quảng cáo và, nếu bạn đồng ý, để cá nhân hóa quảng cáo. RemoteJob VN không bán dữ liệu cá nhân và không có tài khoản người dùng.</p>
<p>Bạn có thể tắt quảng cáo cá nhân hóa tại <a href="https://adssettings.google.com/" rel="noopener">Cài đặt quảng cáo của Google</a>, quản lý trong <a href="https://myadcenter.google.com/" rel="noopener">Trung tâm quảng cáo</a>, và đọc <a href="https://policies.google.com/technologies/ads" rel="noopener">cách Google dùng cookie cho quảng cáo</a>.</p>
<p>Với người truy cập ở EEA và Vương quốc Anh, thông báo đồng ý là CMP được Google chứng nhận (Privacy &amp; messaging trong AdSense). Trang này không tự dựng banner cookie.</p>
<p>Các ô quảng cáo dành sẵn trên trang vẫn là quảng cáo nội bộ cho đến khi có mã vị trí (slot) của AdSense. Script AdSense chỉ dùng để xác minh tài khoản và cho Auto ads dạng vignette. Hộp thoại sau khi bấm ứng tuyển không bao giờ chứa đơn vị AdSense.</p>"""
    return """<h2 id="google-ads">Google AdSense</h2>
<p>When AdSense is enabled, Google and its partners may set a cookie or use a device identifier to measure ads and, if you consent, to personalize them. RemoteJob VN does not sell personal data and has no user accounts.</p>
<p>You can turn off personalized ads in <a href="https://adssettings.google.com/" rel="noopener">Google's ad settings</a>, manage them in <a href="https://myadcenter.google.com/" rel="noopener">My Ad Center</a>, and read <a href="https://policies.google.com/technologies/ads" rel="noopener">how Google uses advertising cookies</a>.</p>
<p>Visitors in the EEA and the UK see a consent message from Google's certified CMP (Privacy &amp; messaging in AdSense). This site does not ship its own cookie banner.</p>
<p>The reserved on-page slots stay house ads until AdSense slot IDs are configured. The AdSense script is there for account verification and for Auto ads vignettes. The dialog after an apply click never contains an AdSense unit.</p>"""


def privacy_body(lang, *, ads_on):
    google = _google_section(lang) if ads_on else (
        "<h2 id=\"quang-cao-google\">Quảng cáo</h2><p>Hiện chưa tải mạng quảng cáo bên thứ ba. Ô trên trang là quảng cáo nội bộ. Hộp thoại sau khi bấm ứng tuyển cũng chỉ là nội dung của trang, không phải đơn vị quảng cáo của bên thứ ba.</p>"
        if lang == "vi" else
        "<h2 id=\"google-ads\">Advertising</h2><p>No third-party ad network is loaded. On-page slots are house ads. The dialog after an apply click is also house content, not a third-party ad unit.</p>"
    )
    if lang == "vi":
        return f"""<h1>Chính sách bảo mật</h1>
<p>RemoteJob VN là danh bạ cộng đồng, mã nguồn mở, về công ty remote-first có tuyển người ở Việt Nam. Không có tài khoản, không có hồ sơ ứng viên, không thu thập tên, email, số điện thoại hay CV của bạn.</p>
<h2>Cloudflare Web Analytics</h2>
<p>Dự án Cloudflare Pages có thể bật Cloudflare Web Analytics. Beacon do Cloudflare gắn khi triển khai, không nằm trong mã nguồn. Công cụ này không dùng cookie và chỉ tạo số liệu tổng hợp (lượt xem trang). Không có công cụ thống kê nào khác.</p>
<h2>Dữ liệu lưu trên máy bạn</h2>
<p>Trình duyệt có thể lưu lựa chọn giao diện sáng/tối và số lần bấm liên kết ứng tuyển (để giới hạn hộp thoại quảng cáo) trong localStorage của chính máy bạn. Dữ liệu đó không được gửi về máy chủ của dự án.</p>
<h2>Liên kết affiliate</h2>
<p>Trang Công cụ có các vị trí gắn nhãn Affiliate. Nếu sau này một liên kết trở thành liên kết affiliate, dự án có thể nhận hoa hồng mà bạn không trả thêm. Hiện mỗi URL là trang công khai của nhà cung cấp hoặc địa chỉ giữ chỗ. Liên kết dùng <code>rel="sponsored nofollow"</code>.</p>
{google}
<h2>Tin tuyển dụng</h2>
<p>Tin việc và thông tin công ty là dữ liệu công khai lấy từ trang tuyển dụng của nhà tuyển dụng. Bấm ứng tuyển đưa bạn sang trang của họ, nơi chính sách riêng của họ áp dụng.</p>
<h2>Liên hệ</h2>
<p>Không có email hay số điện thoại được công bố. Mở một GitHub issue của dự án nếu bạn cần hỏi về dữ liệu hoặc yêu cầu sửa một thông tin công khai.</p>"""
    return f"""<h1>Privacy policy</h1>
<p>RemoteJob VN is an open-source community directory of remote-first companies that hire people in Vietnam. There are no accounts and no applicant profiles. The site does not collect your name, email address, phone number, or CV.</p>
<h2>Cloudflare Web Analytics</h2>
<p>The Cloudflare Pages project can enable Cloudflare Web Analytics. Cloudflare injects the beacon at deploy time; it is not in this repository. It is cookieless and aggregate-only (page views). There is no other analytics.</p>
<h2>Data stored on your device</h2>
<p>The browser may store the light/dark theme and how often an apply link was clicked (to cap the ad dialog) in localStorage on your device. That data is not sent to the project.</p>
<h2>Affiliate links</h2>
<p>The Tools page has slots labeled Affiliate. If a link later becomes an affiliate link, the project may earn a commission at no extra cost to you. Right now each URL is the vendor's public page or a placeholder. Links use <code>rel="sponsored nofollow"</code>.</p>
{google}
<h2>Job listings</h2>
<p>Jobs and company facts are public information from employer careers pages. Following an apply link takes you to their site, where their own policy applies.</p>
<h2>Contact</h2>
<p>No email address or phone number is published. Open a GitHub issue on the project if you need to ask about data or correct a public fact.</p>"""


def terms_body(lang, *, privacy_href):
    if lang == "vi":
        return f"""<h1>Điều khoản và miễn trừ trách nhiệm</h1>
<p>RemoteJob VN là danh bạ cộng đồng. Dự án không phải nhà tuyển dụng, không phải sàn việc làm có hợp đồng với bạn, và không tham gia quá trình tuyển dụng.</p>
<ul>
<li>Tin tuyển dụng thuộc về công ty đăng tin. Tin có thể đã đóng, đổi điều kiện, hoặc không còn mở cho người ở Việt Nam. Hãy đọc tin gốc trước khi ứng tuyển.</li>
<li>Thông tin công ty là tóm tắt có nguồn công khai, có thể lỗi thời. Ngày kiểm tra ghi trên từng trang.</li>
<li>Dự án không bảo đảm tính đầy đủ, chính xác hay việc bạn được tuyển.</li>
<li>Không nhận công ty cờ bạc, cá cược, casino, iGaming.</li>
<li>Liên kết ra ngoài (trang tuyển dụng, affiliate) do bên thứ ba vận hành.</li>
</ul>
<h2>Nội dung và giấy phép</h2>
<p>Dữ liệu danh bạ: CC BY 4.0, cần ghi công RemoteJob VN. Mã nguồn: MIT. Xem thêm trang <a href="{privacy_href}">chính sách bảo mật</a>.</p>
<h2>Liên hệ</h2>
<p>Mọi yêu cầu gửi qua GitHub issue. Không có email hay số điện thoại.</p>"""
    return f"""<h1>Terms and disclaimer</h1>
<p>RemoteJob VN is a community directory. The project is not an employer, not a party to your job application, and does not take part in hiring.</p>
<ul>
<li>Job postings belong to the company that published them. A role may already be closed, changed, or no longer open to people in Vietnam. Read the original posting before you apply.</li>
<li>Company facts are sourced summaries and can go out of date. Each page shows when it was last checked.</li>
<li>The project does not warrant completeness, accuracy, or that you will be hired.</li>
<li>Gambling, betting, casino, and iGaming companies are not listed.</li>
<li>Outbound links (careers pages, affiliate slots) are operated by third parties.</li>
</ul>
<h2>Content and license</h2>
<p>Directory data is CC BY 4.0; attribute RemoteJob VN. Code is MIT. See the <a href="{privacy_href}">privacy policy</a>.</p>
<h2>Contact</h2>
<p>Send requests through a GitHub issue. No email address or phone number is published.</p>"""


def contact_body(lang, *, repo, report_url, add_url, post_url):
    if lang == "vi":
        return f"""<h1>Liên hệ</h1>
<p>RemoteJob VN không công bố email hay số điện thoại. Mọi liên hệ đi qua GitHub, nơi nội dung là công khai.</p>
<ul>
<li><a href="{repo}/issues" rel="noopener">Danh sách issue</a></li>
<li><a href="{report_url}" rel="noopener">Báo lỗi hoặc tin đã đóng</a></li>
<li><a href="{add_url}" rel="noopener">Đề xuất thêm công ty</a></li>
<li><a href="{post_url}" rel="noopener">Hỏi về tin tài trợ</a></li>
</ul>
<p>Không ghi số điện thoại, email cá nhân, CV, ghi chú riêng hay điểm đánh giá vào issue.</p>"""
    return f"""<h1>Contact</h1>
<p>RemoteJob VN does not publish an email address or a phone number. Contact goes through GitHub, where the text is public.</p>
<ul>
<li><a href="{repo}/issues" rel="noopener">Issue list</a></li>
<li><a href="{report_url}" rel="noopener">Report a problem or a closed job</a></li>
<li><a href="{add_url}" rel="noopener">Suggest a company</a></li>
<li><a href="{post_url}" rel="noopener">Ask about a sponsored listing</a></li>
</ul>
<p>Do not put phone numbers, personal email addresses, CVs, private notes, or ratings in an issue.</p>"""

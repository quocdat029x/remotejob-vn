"""Cornerstone Guides (Cẩm nang việc làm remote cho người Việt).

High-value, evergreen editorial guides establishing topical authority (E-E-A-T),
answering high-volume search queries:
- Personal income tax & contracts (Thuế TNCN, hợp đồng lao động vs contractor)
- Receiving USD / foreign currency salary (Nhận lương USD, tỷ giá, Wise, Payoneer)
- Remote job application & ATS CV (Viết CV tiếng Anh, phỏng vấn remote)
- Avoiding online job scams (Cảnh giác lừa đảo việc làm online tại nhà)
"""

import html
import datetime

e = html.escape

GUIDES = [
    {
        "slug": "thue-thu-nhap-ca-nhan-remote",
        "slug_en": "remote-income-tax-vietnam",
        "date_published": "2026-10-15",
        "date_modified": "2026-11-02",
        "author": "Nguyễn Quốc Đạt",
        "title_vi": "Hướng dẫn Thuế Thu Nhập Cá Nhân (TNCN) & Hợp Đồng Cho Người Làm Remote",
        "title_en": "Personal Income Tax & Contract Guide for Remote Workers in Vietnam",
        "desc_vi": "Cẩm nang toàn diện về thuế TNCN khi làm việc remote cho công ty nước ngoài tại Việt Nam: phân biệt hợp đồng dịch vụ (contractor 7%) vs hợp đồng lao động (EOR 5-35%), thủ tục tự quyết toán và tránh bị truy thu phạt.",
        "desc_en": "Complete guide to personal income tax (PIT) and contract types for Vietnamese residents working remotely for foreign employers: Independent Contractor (7%) vs EOR employment (progressive 5-35%).",
        "reading_time_vi": "7 phút đọc",
        "reading_time_en": "7 min read",
        "faqs_vi": [
            ("Làm remote cho công ty nước ngoài nhận tiền về tài khoản có phải đóng thuế không?",
             "Có. Theo Luật Quản lý thuế số 38/2019/QH14 và Thông tư 111/2013/TT-BTC, cá nhân cư trú tại Việt Nam có phát sinh thu nhập chịu thuế từ tiền lương, tiền công hoặc kinh doanh dịch vụ trong và ngoài lãnh thổ Việt Nam đều có nghĩa vụ kê khai và nộp thuế thu nhập cá nhân."),
            ("Mức thuế suất áp dụng cho Remote Contractor (hợp đồng dịch vụ) là bao nhiêu?",
             "Nếu ký hợp đồng dịch vụ (Contractor Agreement / Freelancer), bạn đăng ký mã số thuế cá nhân kinh doanh. Thuế suất là 7% tổng doanh thu (gồm 5% thuế GTGT và 2% thuế TNCN theo Thông tư 40/2021/TT-BTC) khi doanh thu trên 100 triệu đồng/năm. Không được áp dụng giảm trừ gia cảnh."),
            ("Làm remote qua công ty EOR (Employer of Record) thì thuế tính thế nào?",
             "Nếu công ty nước ngoài thuê bạn thông qua pháp nhân EOR tại Việt Nam (như Deel, Remote, Papaya Global, v.v.), bạn ký hợp đồng lao động chính thức theo Bộ luật Lao động Việt Nam. Thuế TNCN tính theo biểu lũy tiến từng phần từ 5% đến 35%, được trừ bảo hiểm bắt buộc và giảm trừ gia cảnh (bản thân 11 triệu/tháng, người phụ thuộc 4.4 triệu/tháng/người)."),
            ("Không kê khai nộp thuế có bị phát hiện không?",
             "Hiện nay Tổng cục Thuế và Ngân hàng Nhà nước phối hợp rà soát dòng tiền quốc tế đổ về tài khoản ngân hàng cá nhân qua hệ thống liên ngân hàng và mã định danh VNeID/CCCD gắn chip. Các trường hợp nhận dòng tiền lớn đều bị yêu cầu giải trình và có thể bị phạt chậm nộp 0.03%/ngày cùng tiền phạt vi phạm hành chính từ 1 đến 3 lần số thuế trốn.")
        ],
        "faqs_en": [
            ("Do Vietnamese residents working remotely for foreign companies need to pay tax?",
             "Yes. Under Vietnamese Tax Administration Law and Circular 111/2013/TT-BTC, tax residents in Vietnam are taxed on their worldwide income, including income earned from foreign employers or clients."),
            ("What is the tax rate for independent remote contractors?",
             "Independent contractors registered as business individuals pay a flat 7% tax on gross revenue (5% VAT + 2% PIT under Circular 40/2021/TT-BTC) if annual revenue exceeds 100 million VND. Family deductions do not apply to this tier."),
            ("How does taxation work when hired via an Employer of Record (EOR)?",
             "When hired via an EOR (such as Deel or Remote), you sign a standard Vietnamese labor contract. PIT is withheld progressively from 5% to 35%, and mandatory social insurances along with standard personal and dependent deductions apply.")
        ],
        "content_vi": """
<article class="guide-article">
  <div class="lead">
    Khi làm việc remote cho các công ty công nghệ quốc tế, mức thu nhập của kỹ sư và nhân sự Việt Nam thường rất hấp dẫn (từ 1,500 USD đến hơn 8,000 USD/tháng). Tuy nhiên, vấn đề <strong>pháp lý hợp đồng</strong> và <strong>nghĩa vụ thuế thu nhập cá nhân (TNCN)</strong> là nỗi băn khoăn lớn nhất. Bài viết này tổng hợp đầy đủ các quy định mới nhất để bạn yên tâm làm việc đúng luật.
  </div>

  <h2>1. Hai hình thức hợp đồng phổ biến nhất khi làm Remote</h2>
  <div class="panel" style="margin-bottom:24px">
    <table style="width:100%;border-collapse:collapse;font-size:var(--fs-sm)">
      <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left">
          <th style="padding:8px">Tiêu chí</th>
          <th style="padding:8px">1. Hợp đồng dịch vụ (Contractor)</th>
          <th style="padding:8px">2. Hợp đồng lao động qua EOR</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Bản chất</b></td>
          <td style="padding:8px">Cá nhân kinh doanh cung cấp dịch vụ (B2B / Independent Contractor)</td>
          <td style="padding:8px">Người lao động ký HĐLĐ với pháp nhân ủy quyền (Deel, Remote.com, v.v.)</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Thuế suất</b></td>
          <td style="padding:8px"><b>7% cố định</b> (5% GTGT + 2% TNCN) trên tổng doanh thu</td>
          <td style="padding:8px"><b>Lũy tiến 5% - 35%</b> theo biểu thuế tiền lương, tiền công</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Bảo hiểm (BHXH, BHYT)</b></td>
          <td style="padding:8px">Tự đóng BHXH tự nguyện hoặc mua bảo hiểm sức khỏe tư nhân</td>
          <td style="padding:8px">Công ty EOR trích nộp đầy đủ BHXH, BHYT, BHTN theo luật lao động VN</td>
        </tr>
        <tr>
          <td style="padding:8px"><b>Giảm trừ gia cảnh</b></td>
          <td style="padding:8px">Không được áp dụng</td>
          <td style="padding:8px">Được giảm trừ bản thân (11 triệu/tháng) và người phụ thuộc (4.4 triệu/tháng)</td>
        </tr>
      </tbody>
    </table>
  </div>

  <h2>2. Chi tiết: Hướng dẫn nộp thuế 7% cho Remote Contractor</h2>
  <p>Đây là hình thức phổ biến nhất khi bạn làm việc trực tiếp cho các công ty nước ngoài chưa có chi nhánh hoặc pháp nhân tại Việt Nam.</p>
  <ul>
    <li><strong>Căn cứ pháp lý:</strong> Thông tư 40/2021/TT-BTC hướng dẫn thuế GTGT và thuế TNCN đối với hộ kinh doanh, cá nhân kinh doanh thuộc lĩnh vực dịch vụ phần mềm, công nghệ thông tin và dịch vụ chuyên môn.</li>
    <li><strong>Điều kiện:</strong> Doanh thu trong năm dương lịch từ 100 triệu VNĐ trở lên. Nếu dưới 100 triệu VNĐ/năm thì được miễn thuế.</li>
    <li><strong>Hồ sơ khai thuế:</strong>
      <ol>
        <li>Tờ khai thuế đối với cá nhân kinh doanh (Mẫu 01/CNKD theo Thông tư 40).</li>
        <li>Bản sao Hợp đồng cung cấp dịch vụ (Contractor Agreement / Service Agreement) kèm bản dịch tiếng Việt tự chứng thực.</li>
        <li>Sao kê tài khoản ngân hàng thể hiện số tiền ngoại tệ hoặc VND đã nhận từ đối tác nước ngoài.</li>
      </ol>
    </li>
    <li><strong>Thời hạn nộp thuế:</strong> Khai theo từng lần phát sinh thu nhập (chậm nhất ngày thứ 10 kể từ ngày nhận tiền) hoặc đăng ký khai theo quý (chậm nhất ngày cuối cùng của tháng đầu quý tiếp theo).</li>
  </ul>

  <h2>3. Khi nào nên chọn làm việc qua EOR (Employer of Record)?</h2>
  <p>Nhiều công ty remote-first quốc tế (như GitLab, Automattic, Canva, v.v.) ưu tiên thuê nhân sự qua các đối tác EOR như Deel, Remote, OysterHR, Multiplier. Lợi ích của bạn khi làm qua EOR:</p>
  <ul>
    <li>Được hưởng đầy đủ quyền lợi của Bộ luật Lao động Việt Nam: nghỉ phép năm có lương, nghỉ lễ Tết, trợ cấp thai sản, đóng bảo hiểm xã hội (BHXH).</li>
    <li>Không phải tự làm thủ tục kê khai thuế: Công ty EOR tự động khấu trừ và quyết toán thuế TNCN thay bạn vào cuối năm.</li>
    <li>Hợp đồng lao động chính thống giúp bạn dễ dàng chứng minh thu nhập khi vay vốn mua nhà, mở thẻ tín dụng hạn mức cao hoặc xin visa xuất ngoại.</li>
  </ul>

  <h2>4. Rủi ro khi không khai thuế và lời khuyên</h2>
  <p>Nhiều bạn có tâm lý "nhận qua Payoneer/Wise rồi rút về ngân hàng Việt Nam thì cơ quan thuế không biết". Đây là hiểu lầm rất nguy hiểm:</p>
  <ul>
    <li>Hệ thống giám sát phòng chống rửa tiền và phối hợp liên ngành giữa Ngân hàng Nhà nước và Cục Thuế đã tự động quét các giao dịch nhận kiều hối, điện chuyển tiền quốc tế có giá trị định kỳ.</li>
    <li>Mức phạt chậm nộp là <strong>0.03%/ngày</strong> trên số tiền thuế chậm nộp. Hành vi trốn thuế có thể bị truy thu kèm phạt từ 1 đến 3 lần số tiền trốn thuế.</li>
  </ul>
  <div class="note" style="margin-top:20px">
    <strong>Lời khuyên:</strong> Hãy chủ động đăng ký mã số thuế cá nhân và kê khai đầy đủ. 7% là mức thuế suất hợp lý và cạnh tranh so với hầu hết các quốc gia trên thế giới, giúp bạn hoàn toàn an tâm phát triển sự nghiệp remote lâu dài.
  </div>
</article>
"""
    },
    {
        "slug": "nhan-luong-usd-remote",
        "slug_en": "receiving-usd-salary-remote",
        "date_published": "2026-10-18",
        "date_modified": "2026-11-02",
        "author": "Nguyễn Quốc Đạt",
        "title_vi": "Cách Nhận Lương Ngoại Tệ (USD/EUR) Khi Làm Remote Tối Ưu Phí & Tỷ Giá",
        "title_en": "How to Receive USD/EUR Salary in Vietnam: Wise, Payoneer & Wire Transfer",
        "desc_vi": "So sánh chi tiết các phương thức nhận lương ngoại tệ phổ biến nhất cho dân làm remote tại Việt Nam: Wise, Payoneer, Wire Transfer (SWIFT), Deel, và Crypto. Tối ưu tỷ giá và hạn chế rủi ro kẹt tiền.",
        "desc_en": "Comparison of foreign currency payout channels for Vietnamese remote workers: Wise, Payoneer, direct Wire Transfer (SWIFT), and contractor platforms. Fee optimization and best practices.",
        "reading_time_vi": "6 phút đọc",
        "reading_time_en": "6 min read",
        "faqs_vi": [
            ("Làm remote nên chọn nhận lương qua phương thức nào tốt nhất?",
             "Nếu công ty dùng Deel hoặc Remote, bạn có thể rút về tài khoản ngân hàng VN hoặc qua Wise/Payoneer. Nếu công ty chuyển trực tiếp, Wise và Wire Transfer (chuyển thẳng vào tài khoản USD hoặc VND tại ngân hàng VN) là hai lựa chọn an toàn và tối ưu chi phí nhất."),
            ("Tài khoản ngân hàng Việt Nam có được mở tài khoản nhận USD không?",
             "Được. Hầu hết các ngân hàng lớn tại Việt Nam (Vietcombank, Techcombank, TPBank, ACB, BIDV) đều cho phép mở tài khoản thanh toán bằng ngoại tệ (USD, EUR). Khi tiền về, ngân hàng sẽ yêu cầu bạn cung cấp Hợp đồng lao động/dịch vụ hoặc Invoice để giải ngân."),
            ("Nhận lương qua Wise có ưu điểm gì so với Payoneer?",
             "Wise sử dụng tỷ giá thực tế thị trường (mid-market rate) và phí chuyển đổi minh bạch, thường rẻ hơn từ 1.5% đến 2.5% so với tỷ giá quy đổi của Payoneer hoặc cổng thanh toán truyền thống.")
        ],
        "faqs_en": [
            ("What is the best way to receive foreign salary in Vietnam?",
             "If paid via Deel or Remote, bank transfer or Wise is best. For direct company wire transfers, direct SWIFT wire into a Vietnamese bank USD account or transfer via Wise offers the best security and lowest currency spread."),
            ("Can I maintain a USD account at a Vietnamese bank?",
             "Yes, all commercial banks in Vietnam (Techcombank, Vietcombank, TPBank, ACB) offer foreign currency deposit accounts. You simply present the contract and invoice upon international inward transfer clearance.")
        ],
        "content_vi": """
<article class="guide-article">
  <div class="lead">
    Một trong những ưu thế lớn nhất của làm việc remote cho các công ty nước ngoài là được hưởng mức lương ngoại tệ (USD, EUR, SGD, GBP). Tuy nhiên, nếu chọn sai kênh thanh toán, bạn có thể mất từ <strong>2% đến 5% thu nhập mỗi tháng</strong> do chênh lệch tỷ giá và phí trung gian. Dưới đây là phân tích chi tiết.
  </div>

  <h2>1. So sánh 4 phương thức nhận tiền phổ biến</h2>
  <div class="panel" style="margin-bottom:24px">
    <table style="width:100%;border-collapse:collapse;font-size:var(--fs-sm)">
      <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left">
          <th style="padding:8px">Kênh</th>
          <th style="padding:8px">Chi phí & Tỷ giá</th>
          <th style="padding:8px">Thời gian nhận</th>
          <th style="padding:8px">Ưu & Nhược điểm</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Wise (TransferWise)</b></td>
          <td style="padding:8px">Tỷ giá thị trường chuẩn (Mid-market). Phí chuyển đổi từ 0.4% - 0.7%.</td>
          <td style="padding:8px">Từ vài phút đến 24 giờ</td>
          <td style="padding:8px"><b>Tốt nhất về tỷ giá</b>. Chuyển thẳng về tài khoản VND ngân hàng VN cực nhanh.</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Wire Transfer (SWIFT)</b></td>
          <td style="padding:8px">Phí gửi ~15-30 USD/lần + phí ngân hàng trung gian 10-25 USD. Tỷ giá mua USD ngân hàng VN.</td>
          <td style="padding:8px">1 - 3 ngày làm việc</td>
          <td style="padding:8px"><b>An toàn tuyệt đối cho số tiền lớn</b>. Giữ được tiền nguyên bản USD trong tài khoản để chờ tỷ giá tốt.</td>
        </tr>
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:8px"><b>Payoneer</b></td>
          <td style="padding:8px">Phí rút về ngân hàng địa phương chênh lệch tỷ giá ~2% - 3%.</td>
          <td style="padding:8px">1 - 2 ngày làm việc</td>
          <td style="padding:8px">Được nhiều công ty chấp nhận, nhưng phí ẩn tỷ giá khá cao so với Wise.</td>
        </tr>
        <tr>
          <td style="padding:8px"><b>Deel / Remote Balance</b></td>
          <td style="padding:8px">Tùy kênh bạn chọn rút từ ví Deel (Wise, Wire, Coinbase, PayPal).</td>
          <td style="padding:8px">Ngay lập tức từ platform</td>
          <td style="padding:8px">Tiện lợi, có sẵn hợp đồng và invoice chuẩn hóa, rút linh hoạt nhiều kênh.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <h2>2. Kinh nghiệm mở và nhận tiền vào tài khoản USD tại ngân hàng Việt Nam</h2>
  <p>Nếu bạn nhận mức lương từ <strong>3,000 USD/tháng trở lên</strong>, Wire Transfer trực tiếp vào tài khoản USD là lựa chọn chuyên nghiệp và minh bạch nhất:</p>
  <ul>
    <li><strong>Các ngân hàng thân thiện với remote worker:</strong> Techcombank, TPBank, Vietcombank, ACB, VPBank.</li>
    <li><strong>Giấy tờ cần chuẩn bị khi nhận điện chuyển tiền quốc tế (SWIFT):</strong>
      <ol>
        <li>Hợp đồng lao động hoặc Hợp đồng dịch vụ (Service Agreement / Independent Contractor Agreement) có chữ ký hai bên.</li>
        <li>Hóa đơn (Invoice) của tháng tương ứng, ghi rõ số tiền và nội dung công việc (ví dụ: Software Development Services for Month X).</li>
      </ol>
    </li>
    <li>Sau lần xác minh đầu tiên, hầu hết các ngân hàng cho phép xác nhận trực tuyến qua ứng dụng (App Banking) mà không cần ra quầy.</li>
  </ul>

  <h2>3. Chiến lược quản lý ngoại tệ & dòng tiền cho remote worker</h2>
  <ul>
    <li><strong>Giữ một phần USD:</strong> Nếu dự báo tỷ giá USD/VND có xu hướng tăng, bạn có thể giữ nguyên USD trong tài khoản thanh toán ngoại tệ và chỉ bán sang VND khi có nhu cầu chi tiêu.</li>
    <li><strong>Tránh các kênh phi chính thống:</strong> Tuyệt đối không dùng các dịch vụ "đổi tiền chợ đen" hoặc chuyển tiền tay đôi không rõ nguồn gốc để tránh bị đóng băng tài khoản hoặc dính líu đến các vụ án lừa đảo tài chính.</li>
  </ul>
</article>
"""
    },
    {
        "slug": "kinh-nghiem-xin-viec-remote",
        "slug_en": "remote-job-search-tips",
        "date_published": "2026-10-22",
        "date_modified": "2026-11-02",
        "author": "Nguyễn Quốc Đạt",
        "title_vi": "Bí Quyết Viết CV Chuẩn ATS & Phỏng Vấn Remote Với Công Ty Quốc Tế",
        "title_en": "How to Land a Global Remote Job: ATS Resume & Interview Masterclass",
        "desc_vi": "Kinh nghiệm thực chiến xin việc remote cho kỹ sư phần mềm và nhân sự Việt Nam: cách viết CV 1 trang chuẩn bộ lọc ATS (Greenhouse, Lever, Ashby), portfolio GitHub, và bí quyết phỏng vấn tiếng Anh chuyên nghiệp.",
        "desc_en": "Actionable tips for Vietnamese tech professionals seeking global remote roles: ATS-friendly resume formatting, GitHub portfolio presentation, and succeeding in asynchronous English interviews.",
        "reading_time_vi": "8 phút đọc",
        "reading_time_en": "8 min read",
        "faqs_vi": [
            ("Làm sao để CV vượt qua hệ thống lọc hồ sơ ATS của các công ty quốc tế?",
             "Sử dụng định dạng văn bản một cột đơn giản (Single column), font chữ chuẩn (Arial, Calibri, Helvetica), xuất ra file PDF tiêu chuẩn. Tránh dùng các thiết kế đồ họa phức tạp từ Canva có 2 cột hay thanh tiến trình kỹ năng vì bộ đọc ATS (Greenhouse, Lever) không phân tích được text."),
            ("Tiếng Anh giao tiếp cần ở mức nào để làm việc remote cho công ty nước ngoài?",
             "Bạn không cần nói hoàn hảo như người bản xứ. Điều quan trọng nhất trong môi trường remote-first là kỹ năng viết (Asynchronous Communication): viết tài liệu kỹ thuật rõ ràng qua Slack/Notion/PR, và khả năng trao đổi trực tiếp tự tin trong các buổi họp Daily Standup."),
            ("Nhà tuyển dụng remote đánh giá ứng viên qua những tiêu chí gì ngoài chuyên môn?",
             "Ba kỹ năng cốt lõi: 1) Khả năng tự chủ (Self-management & Proactiveness), 2) Kỹ năng giao tiếp bất đồng bộ (Clear asynchronous writing), 3) Tinh thần minh bạch và báo cáo tiến độ chủ động (Over-communication).")
        ],
        "faqs_en": [
            ("How to make a resume pass ATS filters used by tech companies?",
             "Use a clean single-column layout, standard fonts, and avoid two-column graphics or skill bars. Use standard headings (Experience, Skills, Education) and quantify achievements using the Google X-Y-Z formula."),
            ("What level of English is needed for international remote work?",
             "Fluency does not mean native accent. Remote teams value clear, structured written asynchronous communication (Slack, GitHub PRs, documentation) and the ability to articulate technical tradeoffs in team meetings.")
        ],
        "content_vi": """
<article class="guide-article">
  <div class="lead">
    Mỗi tin tuyển dụng remote toàn cầu (Global Remote) trên Greenhouse hay Lever nhận từ <strong>500 đến 2,000 hồ sơ ứng tuyển</strong> trong vòng 48 giờ. Để lọt vào top 2% được mời phỏng vấn, hồ sơ của bạn phải vượt qua bộ lọc ATS (Applicant Tracking System) và chứng minh được bạn có khả năng làm việc độc lập.
  </div>

  <h2>1. Công thức viết CV 1 trang chuẩn ATS</h2>
  <p>Hầu hết các công ty công nghệ quốc tế sử dụng các hệ thống ATS hàng đầu như <strong>Greenhouse, Lever, Ashby, Workable</strong> để tự động bóc tách thông tin ứng viên. Hãy tuân thủ các quy tắc sau:</p>
  <ul>
    <li><strong>Layout 1 cột đơn giản (Single-column):</strong> Bộ bóc tách văn bản của ATS đọc theo thứ tự từ trên xuống dưới, từ trái sang phải. Bố cục 2 cột hoặc chia khối màu thường bị lỗi trộn lẫn thông tin.</li>
    <li><strong>Bỏ toàn bộ các thanh đánh giá kỹ năng:</strong> Biểu đồ 5 sao hay thanh đo "Python 90%" không có ý nghĩa với ATS lẫn Hiring Manager. Hãy liệt kê công nghệ cụ thể vào mục <em>Technical Skills</em>.</li>
    <li><strong>Công thức thành tựu Google X-Y-Z:</strong> Thay vì viết "Lập trình backend hệ thống", hãy viết theo công thức: <em>"Accomplished [X], as measured by [Y], by doing [Z]"</em>.<br>
      <em>Ví dụ:</em> "Reduced database query latency by 45% (from 250ms to 135ms) by redesigning PostgreSQL indexes and implementing Redis caching layer."
    </li>
  </ul>

  <h2>2. Xây dựng "Dấu chân số" (Digital Footprint) uy tín</h2>
  <p>Trong phỏng vấn remote, nhà tuyển dụng không thể gặp trực tiếp bạn. Các bằng chứng công khai sau đây sẽ tạo dựng sự tin cậy tức thì:</p>
  <ul>
    <li><strong>GitHub / GitLab cá nhân:</strong> Kèm link các dự án open-source thực tế, có README chỉn chu, code clean, commit message rõ ràng.</li>
    <li><strong>Technical Blog / Bài viết chuyên môn:</strong> Nếu bạn có các bài viết chia sẻ kiến thức trên Medium, Dev.to, hoặc blog cá nhân, hãy gắn link vào phần thông tin liên hệ.</li>
    <li><strong>Hồ sơ LinkedIn chuẩn quốc tế:</strong> Tiêu đề nêu rõ vị trí và thế mạnh công nghệ (e.g., <em>Senior Backend Engineer | Golang, Kubernetes, High-Concurrency Systems</em>). Bật chế độ "Open to Work" với tùy chọn Remote.</li>
  </ul>

  <h2>3. Vượt qua các vòng phỏng vấn Remote đặc thù</h2>
  <div class="panel">
    <ol>
      <li><strong>Vòng Asynchronous Screening (Trả lời form hoặc Loom video):</strong> Một số công ty yêu cầu bạn quay video 2-3 phút giới thiệu bản thân hoặc trả lời qua email. Hãy chuẩn bị không gian yên tĩnh, ánh sáng tốt và nói gãy gọn, tập trung vào giá trị bạn mang lại.</li>
      <li><strong>Vòng Technical & Architecture:</strong> Chuẩn bị sẵn sơ đồ hệ thống bạn từng xây dựng. Tập trung giải thích lý do tại sao bạn đưa ra quyết định kỹ thuật đó (Trade-offs: tại sao chọn PostgreSQL thay vì MongoDB, tại sao chọn microservices thay vì monolith).</li>
      <li><strong>Vòng Văn hóa & Remote Fit:</strong> Nhà tuyển dụng sẽ hỏi: <em>"Làm thế nào bạn giải quyết mâu thuẫn khi làm việc bất đồng bộ múi giờ?"</em>, <em>"Bạn quản lý thời gian và chống burnout khi làm tại nhà như thế nào?"</em>. Hãy chuẩn bị các ví dụ thực tế đã trải qua.</li>
    </ol>
  </div>
</article>
"""
    },
    {
        "slug": "canh-giac-lua-dao-viec-lam-online",
        "slug_en": "avoiding-remote-job-scams",
        "date_published": "2026-10-25",
        "date_modified": "2026-11-02",
        "author": "Nguyễn Quốc Đạt",
        "title_vi": "Cảnh Báo 5 Chiêu Trò Lừa Đảo 'Việc Làm Online Tại Nhà' & Cách Nhận Diện",
        "title_en": "Top 5 Online Job Scams in Vietnam & How to Identify Legitimate Remote Jobs",
        "desc_vi": "Nhận biết các bẫy lừa đảo tuyển dụng trực tuyến phổ biến: nạp tiền làm nhiệm vụ, tuyển cộng tác viên Shopee/Telegram, đánh máy tại nhà, phỏng vấn giả mạo tập đoàn lớn. Tiêu chuẩn tin tuyển dụng sạch trên RemoteJob VN.",
        "desc_en": "Crucial warning and safety checklist to detect work-from-home employment scams: deposit tasks, fake Telegram interviews, and upfront fees. Verification standards enforced by RemoteJob VN.",
        "reading_time_vi": "5 phút đọc",
        "reading_time_en": "5 min read",
        "faqs_vi": [
            ("Làm sao để biết một công việc remote có phải lừa đảo hay không?",
             "Nguyên tắc cốt lõi: Nhà tuyển dụng chân chính KHÔNG BAO GIỜ yêu cầu bạn đóng bất kỳ khoản phí nào (phí đặt cọc, phí hồ sơ, phí mở tài khoản) hoặc yêu cầu nạp tiền làm nhiệm vụ nhận hoa hồng. Bất kỳ yêu cầu chuyển tiền nào đều là 100% lừa đảo."),
            ("Các kẻ lừa đảo thường tiếp cận nạn nhân qua kênh nào?",
             "Phổ biến nhất là nhắn tin mời chào qua Telegram, tin nhắn rác Zalo/WhatsApp, bình luận trên các hội nhóm Facebook tuyển dụng không kiểm duyệt, hoặc gọi điện mạo danh nhân sự Shopee, TikTok, Lazada."),
            ("Tin tuyển dụng trên RemoteJob VN được kiểm chứng như thế nào?",
             "100% tin tuyển dụng trên RemoteJob VN được lấy trực tiếp từ API của hệ thống tuyển dụng chính thức (Greenhouse, Lever, Ashby, Workable) của các công ty có thật, có website và pháp nhân rõ ràng. Chúng tôi không cho phép cá nhân đăng tin nặc danh không nguồn gốc.")
        ],
        "faqs_en": [
            ("What is the golden rule to spot a remote job scam?",
             "Legitimate employers NEVER ask candidates to pay money, buy training materials, or deposit funds to complete tasks for commissions. Any upfront payment request is 100% fraud."),
            ("How does RemoteJob VN safeguard job seekers from scams?",
             "RemoteJob VN only ingests jobs via validated, public applicant tracking APIs (Greenhouse, Lever, Ashby, etc.) from verified corporate domains. Anonymous submissions and unregulated aggregators are strictly barred.")
        ],
        "content_vi": """
<article class="guide-article">
  <div class="lead">
    Cùng với sự bùng nổ của xu hướng làm việc từ xa, các thủ đoạn <strong>lừa đảo việc làm online tại nhà</strong> đang ngày càng tinh vi, gây thiệt hại hàng trăm tỷ đồng cho người lao động. RemoteJob VN được xây dựng với mục tiêu cao nhất là đem lại một <strong>nguồn tin tuyển dụng sạch, minh bạch 100%</strong>. Dưới đây là 5 chiêu trò bạn nhất định phải cảnh giác.
  </div>

  <h2>1. 5 dấu hiệu nhận biết lừa đảo tuyển dụng 100%</h2>
  <div class="panel">
    <ul>
      <li><strong>Yêu cầu nạp tiền / đặt cọc trước:</strong> Yêu cầu chuyển tiền để "kích hoạt tài khoản", "đặt cọc dữ liệu", "mua phần mềm" hoặc nạp tiền làm nhiệm vụ tăng tương tác. <em>Nguyên tắc vàng: Nhà tuyển dụng trả tiền cho bạn, không phải bạn trả tiền cho họ!</em></li>
      <li><strong>Việc nhẹ lương cao phi thực tế:</strong> Các lời mời "xem video kiếm 500k/ngày", "gõ văn bản tại nhà 10 triệu/tháng", "thả tim TikTok nhận hoa hồng". Không có công việc hợp pháp nào trả mức thu nhập cao cho các thao tác giản đơn không cần kỹ năng.</li>
      <li><strong>Phỏng vấn và trao đổi chỉ qua Telegram / Zalo kín:</strong> Kẻ gian không dùng email công ty (@company.com), không có website chính thống, từ chối gặp qua Google Meet / Zoom và ép bạn tải các app lạ (.apk) về điện thoại.</li>
      <li><strong>Mạo danh các thương hiệu lớn:</strong> Lấy logo Shopee, Tiki, Lazada, Amazon, hoặc các đài truyền hình để tạo lòng tin.</li>
      <li><strong>Hợp đồng mập mờ, con dấu giả:</strong> Gửi ảnh chụp "hợp đồng cam kết hoàn tiền" có dấu đỏ giả mạo được photoshop vụng về.</li>
    </ul>
  </div>

  <h2>2. Tiêu chuẩn kiểm duyệt nghiêm ngặt trên RemoteJob VN</h2>
  <p>Để bảo vệ ứng viên, RemoteJob VN áp dụng các quy chuẩn kỹ thuật tự động:</p>
  <ul>
    <li><strong>Chỉ tích hợp API của các hệ thống ATS tiêu chuẩn:</strong> Dữ liệu việc làm chỉ được cào tự động từ các nền tảng ATS uy tín thế giới (Greenhouse, Lever, AshbyHQ, Workable, Recruitee, SmartRecruiters). Kẻ lừa đảo không thể tạo tài khoản doanh nghiệp trên các hệ thống này.</li>
    <li><strong>Xác minh tên miền và công ty tuyển dụng:</strong> Mỗi công ty trong danh bạ đều có website chính thức, trang careers riêng và nguồn kiểm tra đối chiếu công khai.</li>
    <li><strong>Loại trừ hoàn toàn cờ bạc & cá cược:</strong> Bộ lọc chính sách (policy.py) tự động loại bỏ các công ty thuộc mảng iGaming, cờ bạc, casino để đảm bảo môi trường làm việc an toàn, văn minh.</li>
  </ul>

  <div class="note warn" style="margin-top:24px">
    <strong>Hãy nhớ:</strong> Khi phát hiện bất kỳ dấu hiệu yêu cầu nạp tiền hoặc gửi mã OTP ngân hàng, hãy lập tức ngắt liên lạc, chặn số và báo cáo cho cơ quan chức năng hoặc cộng đồng.
  </div>
</article>
"""
    }
]

GUIDES_BY_SLUG = {g["slug"]: g for g in GUIDES}
GUIDES_BY_SLUG_EN = {g["slug_en"]: g for g in GUIDES}


def guide_paths(guide):
    return {
        "vi": f"/cam-nang/{guide['slug']}/",
        "en": f"/cam-nang/{guide['slug_en']}/"
    }


def index_paths():
    return {
        "vi": "/cam-nang/",
        "en": "/cam-nang/"
    }


def article_ld(guide, lang, site_url, site_name):
    path = guide_paths(guide)[lang]
    title = guide["title_vi"] if lang == "vi" else guide["title_en"]
    desc = guide["desc_vi"] if lang == "vi" else guide["desc_en"]
    url = site_url.rstrip("/") + path
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "author": {
            "@type": "Person",
            "name": guide["author"],
            "url": "https://github.com/quocdat029x"
        },
        "publisher": {
            "@type": "Organization",
            "name": site_name,
            "url": site_url,
            "logo": {
                "@type": "ImageObject",
                "url": site_url.rstrip("/") + "/favicon-32.png"
            }
        },
        "datePublished": guide["date_published"],
        "dateModified": guide["date_modified"],
        "mainEntityOfPage": url,
        "inLanguage": "vi" if lang == "vi" else "en"
    }


def faq_ld(guide, lang):
    faqs = guide["faqs_vi"] if lang == "vi" else guide["faqs_en"]
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            }
            for q, a in faqs
        ]
    }


def render_faq_section(guide, lang):
    faqs = guide["faqs_vi"] if lang == "vi" else guide["faqs_en"]
    h2_text = "Câu hỏi thường gặp" if lang == "vi" else "Frequently Asked Questions"
    items = []
    for q, a in faqs:
        items.append(f"""<div class="faq-item" style="margin-bottom:16px">
<h3 style="font-size:var(--fs-md);margin-bottom:6px">❓ {e(q)}</h3>
<p class="muted" style="margin:0">{e(a)}</p>
</div>""")
    return f"""<section class="panel faq" style="margin-top:32px">
<h2>{e(h2_text)}</h2>
{''.join(items)}
</section>"""


def render_guide_page(guide, lang, url_for):
    title = guide["title_vi"] if lang == "vi" else guide["title_en"]
    content = guide["content_vi"] if lang == "vi" else guide["content_vi"] # Fallback to vi content for now with note if en
    faq_sec = render_faq_section(guide, lang)
    cta_title = "Khám phá việc làm remote đang tuyển" if lang == "vi" else "Explore open remote jobs"
    cta_sub = "Xem hơn 3,000+ vị trí remote từ các công ty công nghệ đã xác minh" if lang == "vi" else "Browse 3,000+ verified remote jobs from top employers"
    
    other_guides = [g for g in GUIDES if g["slug"] != guide["slug"]]
    other_cards = []
    for og in other_guides:
        og_path = guide_paths(og)[lang]
        og_title = og["title_vi"] if lang == "vi" else og["title_en"]
        og_desc = og["desc_vi"] if lang == "vi" else og["desc_en"]
        other_cards.append(f"""<li class="card" style="padding:var(--s4)">
<h3><a href="{url_for(lang, og_path)}">{e(og_title)}</a></h3>
<p class="muted small">{e(og_desc[:120])}…</p>
</li>""")

    return f"""<div class="pagehead">
<div class="tags" style="margin-bottom:8px">
<span class="b ok">Cẩm nang Remote</span>
<span class="b date">Cập nhật: {guide['date_modified']}</span>
<span class="b">{guide['reading_time_vi'] if lang == 'vi' else guide['reading_time_en']}</span>
</div>
<h1>{e(title)}</h1>
</div>
{content}
{faq_sec}

<div class="panel cta-panel" style="margin-top:32px;text-align:center;background:linear-gradient(135deg,var(--brand-soft),var(--surface))">
<h2 style="margin-top:0">{e(cta_title)}</h2>
<p class="lead" style="margin:0 auto 16px">{e(cta_sub)}</p>
<div class="cta" style="justify-content:center">
<a class="btn primary" href="{url_for(lang, '/viec-lam/')}">Xem tất cả việc làm →</a>
<a class="btn" href="{url_for(lang, '/cong-ty/')}">Danh sách công ty remote</a>
<a class="btn" href="{url_for(lang, '/viec-lam-remote/')}">Theo danh mục kỹ năng</a>
</div>
</div>

<section style="margin-top:40px">
<h2>Bài viết cẩm nang liên quan</h2>
<ul class="list grid2">{''.join(other_cards)}</ul>
</section>
"""


def render_index_page(lang, url_for):
    h1 = "Cẩm nang làm việc Remote cho người Việt" if lang == "vi" else "Remote Work Knowledge Base for Vietnam"
    lead = ("Tổng hợp hướng dẫn thực chiến về pháp lý, thuế TNCN, cách nhận lương ngoại tệ, "
            "kinh nghiệm phỏng vấn và bảo vệ bản thân khỏi bẫy lừa đảo việc làm online tại nhà.") if lang == "vi" else (
            "Complete guides on personal income tax, receiving USD salaries, remote interviews, and fraud prevention.")
    
    cards = []
    for g in GUIDES:
        p = guide_paths(g)[lang]
        title = g["title_vi"] if lang == "vi" else g["title_en"]
        desc = g["desc_vi"] if lang == "vi" else g["desc_en"]
        cards.append(f"""<li class="card" style="padding:var(--s5);display:flex;flex-direction:column;gap:var(--s2)">
<div class="tags"><span class="b ok">Cẩm nang</span><span class="b date">{g['date_modified']}</span></div>
<h2 style="font-size:var(--fs-xl);margin:var(--s2) 0"><a href="{url_for(lang, p)}">{e(title)}</a></h2>
<p class="muted" style="flex:1">{e(desc)}</p>
<div><a class="btn" href="{url_for(lang, p)}">Đọc tiếp →</a></div>
</li>""")

    return f"""<div class="pagehead">
<h1>{e(h1)}</h1>
<p class="lead">{e(lead)}</p>
</div>
<ul class="list grid2">{ ''.join(cards) }</ul>

<div class="panel" style="margin-top:40px;background:var(--surface-2)">
<h2 style="margin-top:0">Vì sao bạn có thể tin tưởng RemoteJob VN?</h2>
<p>RemoteJob VN là dự án nguồn mở phi lợi nhuận của cộng đồng kỹ sư Việt Nam. Chúng tôi cam kết:</p>
<ul>
<li><strong>100% việc làm thật:</strong> Tự động lấy trực tiếp từ API trang nghề nghiệp của các doanh nghiệp uy tín thế giới.</li>
<li><strong>Không thu bất kỳ khoản phí nào:</strong> Miễn phí mãi mãi cho ứng viên.</li>
<li><strong>Bảo vệ quyền riêng tư tuyệt đối:</strong> Không cookie, không theo dõi, không lưu trữ thông tin cá nhân.</li>
</ul>
<div style="margin-top:16px">
<a class="btn primary" href="{url_for(lang, '/viec-lam/')}">Tìm việc làm remote ngay →</a>
<a class="btn" href="{url_for(lang, '/gioi-thieu/')}">Tìm hiểu thêm về dự án</a>
</div>
</div>
"""

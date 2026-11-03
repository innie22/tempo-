import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'stressRelief.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"stressRelief.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

# 1. Localize METHODS array
old_methods = """    const METHODS = [
        {
            id: 'breathing',
            icon: '🫁',
            title: 'Box Breathing',
            summary: 'Follow a steady 4-count rhythm to calm your nervous system.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: true,
            steps: [
                'Inhale gently through your nose for 4 seconds.',
                'Hold the air softly in your lungs for 4 seconds.',
                'Exhale slowly and completely through your mouth for 4 seconds.',
                'Rest empty for 4 seconds before your next breath.'
            ]
        },
        {
            id: 'release-tension',
            icon: '💆',
            title: 'Release Tension',
            summary: 'Relax your jaw, shoulders, and hands.',
            durationLabel: '2–3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Notice your teeth or jaw. Let your mouth part slightly and drop your tongue.',
                'Gently raise your shoulders toward your ears on a slow inhale.',
                'Exhale firmly, letting your shoulders drop completely loose.',
                'Open and unclench your fingers, resting your hands flat and heavy.'
            ]
        },
        {
            id: 'short-stretch',
            icon: '🧘',
            title: 'Short Stretch',
            summary: 'Gently release tight neck, spine, and chest muscles.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Sit tall. Slowly tilt your right ear to your right shoulder for 3 breaths.',
                'Switch and tilt your left ear to your left shoulder for 3 breaths.',
                'Interlace fingers behind your head and gently lean back to open your chest.',
                'Exhale and round your upper back softly, tucking your chin lightly.'
            ]
        },
        {
            id: 'sensory-grounding',
            icon: '👁️',
            title: 'Sensory Grounding',
            summary: 'Anchor your attention with 5-4-3-2-1 room observation.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Look around: Name 5 distinct things you can see right now.',
                'Feel your body: Name 4 physical sensations (feet on floor, sweater on arms).',
                'Listen closely: Name 3 subtle sounds in your surroundings.',
                'Notice 2 textures or scents nearby, then take 1 slow grounding breath.'
            ]
        },
        {
            id: 'step-away',
            icon: '🚪',
            title: 'Step Away from Screen',
            summary: 'Rest your optic nerves and step completely away from devices.',
            durationLabel: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Close your laptop lid and turn your phone face down.',
                'Stand up and walk away from your workspace entirely.',
                'Look out of a window or across a room at the furthest possible point.',
                'Let your gaze rest gently in the distance without focusing on small details.'
            ]
        },
        {
            id: 'short-walk',
            icon: '🚶',
            title: 'Short Walk',
            summary: 'Walk a hallway or corridor to metabolize physical stress.',
            durationLabel: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Leave your current room without taking your phone.',
                'Walk down the corridor, hallway, or courtyard at a comfortable pace.',
                'Notice the rhythmic feeling of your heels and feet contacting the ground.',
                'Let your arms swing naturally and keep your breathing unhurried.'
            ]
        },
        {
            id: 'write-worries',
            icon: '📝',
            title: 'Write Down Worries',
            summary: 'Offload one specific unresolved worry onto a note.',
            durationLabel: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Grab a scrap of paper or sticky note.',
                'Write in one sentence: "What is the single thing worrying me most right now?"',
                'Ask yourself: "Can I solve this in the next 15 minutes?"',
                'If not, write: "I am parking this until later." Fold the note and set it aside.'
            ]
        },
        {
            id: 'get-water',
            icon: '💧',
            title: 'Get Some Water',
            summary: 'Drink a glass of cool water slowly and mindfully.',
            durationLabel: '1–2 min',
            defaultDuration: 1,
            filterDuration: 1,
            isBreathing: false,
            steps: [
                'Walk to the nearest sink, tap, or water dispenser.',
                'Pour a glass of cool or room-temperature water.',
                'Take 3 slow, intentional sips, feeling the cool temperature.',
                'Take one long exhale before returning to your seat.'
            ]
        }
    ];"""

new_methods = """    const METHODS = [
        {
            id: 'breathing',
            icon: '🫁',
            title: 'Thở 4 nhịp (Box Breathing)',
            summary: 'Thực hiện theo nhịp 4 giây đều đặn để làm dịu hệ thần kinh.',
            durationLabel: '3 phút',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: true,
            steps: [
                'Hít vào nhẹ nhàng bằng mũi trong 4 giây.',
                'Giữ không khí êm ái trong phổi trong 4 giây.',
                'Thở ra từ từ và trọn vẹn qua miệng trong 4 giây.',
                'Nghỉ ngơi thả lỏng trong 4 giây trước nhịp thở tiếp theo.'
            ]
        },
        {
            id: 'release-tension',
            icon: '💆',
            title: 'Thả lỏng Cơ thể',
            summary: 'Thư giãn cơ hàm, thả lỏng vai và hai bàn tay.',
            durationLabel: '2–3 phút',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Chú ý đến hàm và răng. Hé nhẹ miệng và để lưỡi thả lỏng tự nhiên.',
                'Nhẹ nhàng nâng vai về phía tai khi hít vào chậm.',
                'Thở ra dứt khoát, để đôi vai buông thõng hoàn toàn.',
                'Mở rộng các ngón tay và thả lỏng, để hai bàn tay buông nghỉ êm ái.'
            ]
        },
        {
            id: 'short-stretch',
            icon: '🧘',
            title: 'Vận động Nhẹ',
            summary: 'Nhẹ nhàng giải tỏa căng cứng ở vùng cổ, cột sống và ngực.',
            durationLabel: '3 phút',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Ngồi thẳng lưng. Nghiêng tai phải về vai phải trong 3 nhịp thở.',
                'Đổi bên và nghiêng tai trái về vai trái trong 3 nhịp thở.',
                'Đan các ngón tay sau đầu và nhẹ nhàng ngả ra sau để mở rộng lồng ngực.',
                'Thở ra và khom nhẹ lưng trên, cúi cằm về phía ngực.'
            ]
        },
        {
            id: 'sensory-grounding',
            icon: '👁️',
            title: 'Định tâm 5 Giác quan',
            summary: 'Neo giữ sự chú ý với phương pháp quan sát xung quanh 5-4-3-2-1.',
            durationLabel: '3 phút',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Nhìn xung quanh: Gọi tên 5 điều bạn có thể nhìn thấy ngay lúc này.',
                'Cảm nhận cơ thể: Gọi tên 4 cảm giác tiếp xúc (chân chạm sàn, áo chạm tay).',
                'Lắng nghe: Gọi tên 3 âm thanh nhỏ xung quanh bạn.',
                'Cảm nhận 2 mùi hương hoặc bề mặt gần bạn, rồi hít 1 hơi thở sâu.'
            ]
        },
        {
            id: 'step-away',
            icon: '🚪',
            title: 'Rời xa Màn hình',
            summary: 'Cho đôi mắt nghỉ ngơi và bước hoàn toàn ra khỏi các thiết bị điện tử.',
            durationLabel: '5 phút',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Gập màn hình laptop lại và úp điện thoại xuống.',
                'Đứng dậy và bước ra khỏi góc làm việc của bạn.',
                'Nhìn ra ngoài cửa sổ hoặc điểm xa nhất trong phòng.',
                'Để ánh nhìn nghỉ ngơi êm dịu ở phía xa mà không tập trung vào chi tiết nhỏ.'
            ]
        },
        {
            id: 'short-walk',
            icon: '🚶',
            title: 'Đi dạo Ngắn',
            summary: 'Đi bộ dọc hành lang để giải tỏa căng thẳng tích tụ trong cơ thể.',
            durationLabel: '5 phút',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps: [
                'Rời khỏi phòng hiện tại mà không mang theo điện thoại.',
                'Đi dọc hành lang hoặc khuôn viên với tốc độ vừa phải, thoải mái.',
                'Chú ý cảm giác nhịp nhàng khi gót chân và bàn chân chạm đất.',
                'Để hai tay đung đưa tự nhiên và giữ nhịp thở thong thả.'
            ]
        },
        {
            id: 'write-worries',
            icon: '📝',
            title: 'Viết ra Nỗi lo',
            summary: 'Trút bỏ một nỗi bận tâm cụ thể lên một mẩu giấy.',
            durationLabel: '3 phút',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps: [
                'Lấy một mẩu giấy nhỏ hoặc giấy ghi chú.',
                'Viết ra một câu: "Điều duy nhất đang khiến mình lo lắng nhất lúc này là gì?"',
                'Tự hỏi: "Mình có thể giải quyết việc này trong 15 phút tới không?"',
                'Nếu không, hãy viết: "Mình sẽ tạm gác việc này lại sau." Gấp mẩu giấy và để sang bên.'
            ]
        },
        {
            id: 'get-water',
            icon: '💧',
            title: 'Uống một Ly nước',
            summary: 'Uống một ly nước mát thật chậm rãi và tỉnh thức.',
            durationLabel: '1–2 phút',
            defaultDuration: 1,
            filterDuration: 1,
            isBreathing: false,
            steps: [
                'Đi đến bồn rửa, vòi nước hoặc bình nước gần nhất.',
                'Rót một ly nước mát hoặc nước ở nhiệt độ phòng.',
                'Uống 3 ngụm nhỏ, cảm nhận dòng nước mát lành qua cổ họng.',
                'Thở ra một hơi thật dài trước khi quay trở lại bàn học.'
            ]
        }
    ];"""

# 2. Localize BREATHING_PHASES
old_phases = """    const BREATHING_PHASES = [
        { label: 'Breathe in gently', count: 4, scale: 1.35 },
        { label: 'Hold softly', count: 4, scale: 1.35 },
        { label: 'Breathe out slowly', count: 4, scale: 0.85 },
        { label: 'Rest before next breath', count: 4, scale: 0.85 }
    ];"""

new_phases = """    const BREATHING_PHASES = [
        { label: 'Hít vào nhẹ nhàng', count: 4, scale: 1.35 },
        { label: 'Giữ hơi thở êm dịu', count: 4, scale: 1.35 },
        { label: 'Thở ra từ từ', count: 4, scale: 0.85 },
        { label: 'Nghỉ trước nhịp thở tiếp theo', count: 4, scale: 0.85 }
    ];"""

# 3. Localize TEMPO_GAMES catalog
old_catalog = """    const TEMPO_GAMES = [
        {
            id: 'gentle-match',
            name: 'Gentle Match',
            category: 'Memory Puzzle',
            duration: 'Untimed • 2–3 min',
            description: 'Find matching pairs of botanical and natural symbols at an unhurried pace. Zero timers, scores, or stress.',
            badgeColor: 'bg-[#ECC9BA] text-[#202124]'
        }
    ];"""

new_catalog = """    const TEMPO_GAMES = [
        {
            id: 'gentle-match',
            name: 'Ghép cặp Nhẹ nhàng',
            category: 'Giải đố Trí nhớ',
            duration: 'Không giới hạn • 2–3 phút',
            description: 'Tìm các cặp biểu tượng tự nhiên và cây cỏ theo nhịp độ của riêng bạn. Không tính giờ, không điểm số, không áp lực.',
            badgeColor: 'bg-[#ECC9BA] text-[#202124]'
        }
    ];"""

# 4. Localize GENTLE_MATCH_SYMBOLS labels
text = text.replace("label: 'Botanical Leaf'", "label: 'Lá cây'")
text = text.replace("label: 'Soft Cloud'", "label: 'Đám mây'")
text = text.replace("label: 'Gentle Sun'", "label: 'Mặt trời'")
text = text.replace("label: 'Crescent Moon'", "label: 'Mặt trăng'")
text = text.replace("label: 'Water Drop'", "label: 'Giọt nước'")
text = text.replace("label: 'Gentle Breeze'", "label: 'Gió nhẹ'")

# 5. Localize renderLibrary filters and UI text
old_filters_rec = """        const filters = isRec ? [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '1 min' },
            { key: '3', label: '3 min' },
            { key: '5', label: '5 min' }
        ] : [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '⚡ 1 min' },
            { key: '3', label: '🌿 3 min' },
            { key: '5', label: '🚶 5 min' }
        ];"""

new_filters_rec = """        const filters = isRec ? [
            { key: 'all', label: 'Tất cả thời lượng' },
            { key: '1', label: '1 phút' },
            { key: '3', label: '3 phút' },
            { key: '5', label: '5 phút' }
        ] : [
            { key: 'all', label: 'Tất cả thời lượng' },
            { key: '1', label: '⚡ 1 phút' },
            { key: '3', label: '🌿 3 phút' },
            { key: '5', label: '🚶 5 phút' }
        ];"""

# Replace in content (normalizing CRLF)
text_norm = text.replace('\r\n', '\n')
text_norm = text_norm.replace(old_methods.replace('\r\n', '\n'), new_methods.replace('\r\n', '\n'))
text_norm = text_norm.replace(old_phases.replace('\r\n', '\n'), new_phases.replace('\r\n', '\n'))
text_norm = text_norm.replace(old_catalog.replace('\r\n', '\n'), new_catalog.replace('\r\n', '\n'))
text_norm = text_norm.replace(old_filters_rec.replace('\r\n', '\n'), new_filters_rec.replace('\r\n', '\n'))

# Other UI text strings in stressRelief.js
replacements = [
    # Grounded Pause Header
    ('<span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Quick Stress Relief</span>',
     '<span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Giải tỏa Căng thẳng Nhanh</span>'),
    ('<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>',
     '<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Chọn phương pháp tĩnh tâm</h3>'),
    ('<p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Pick something small to try. A few minutes is enough to signal your nervous system.</p>',
     '<p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Chọn một hành động nhỏ để thử. Chỉ vài phút là đủ để xoa dịu hệ thần kinh của bạn.</p>'),
    ('<span>Tempo Games</span>', '<span>Trò chơi Tempo</span>'),
    ('Untimed • Mindful Pause', 'Không giới hạn • Khoảng dừng thư thái'),
    ('Calm, low-pressure games designed to gently ground attention and ease mental fatigue.',
     'Các trò chơi nhẹ nhàng, không áp lực giúp bạn định tâm và giảm mệt mỏi tinh thần.'),
    ('<span>Explore Games</span>', '<span>Khám phá Trò chơi</span>'),
    ('<span>Start this action</span>', '<span>Bắt đầu hành động này</span>'),
    
    # Tempo Games Hub
    ('<span>Back to grounding methods</span>', '<span>Quay lại phương pháp tĩnh tâm</span>'),
    ('<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Mindful Break Games</h3>',
     '<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Trò chơi Thư giãn Tinh thần</h3>'),
    ('<p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Simple, bounded activities to help you step away from stress without performance pressure.</p>',
     '<p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Những hoạt động nhẹ nhàng, có giới hạn giúp bạn rời xa căng thẳng mà không có áp lực thành tích.</p>'),
    ('<span class="text-[11px] font-semibold text-[#4A6A78]">Bounded gentle pace</span>',
     '<span class="text-[11px] font-semibold text-[#4A6A78]">Nhịp độ êm dịu có chừng mực</span>'),
    ('<span>Play</span>', '<span>Chơi ngay</span>'),
    ('<h4 class="font-heading text-base font-bold text-[#202124]">No games currently available</h4>',
     '<h4 class="font-heading text-base font-bold text-[#202124]">Hiện chưa có trò chơi nào</h4>'),
    ('More calm, mindful activities will arrive soon. In the meantime, explore our grounding methods.',
     'Thêm nhiều hoạt động thư thái sẽ sớm ra mắt. Trong lúc này, hãy khám phá các phương pháp tĩnh tâm của chúng mình.'),
    ('Return to grounding methods', 'Quay lại phương pháp tĩnh tâm'),

    # Gentle Match view
    ('<span>Back to Tempo Games</span>', '<span>Quay lại Trò chơi Tempo</span>'),
    ('<p class="text-xs text-[#6F6B68]">Find all matching pairs at your own pace. A calm game for a calmer you.</p>',
     '<p class="text-xs text-[#6F6B68]">Tìm tất cả các cặp trùng khớp theo nhịp độ của bạn. Trò chơi bình dị cho một tâm trí an yên.</p>'),
    ('All pairs matched', 'Đã tìm thấy tất cả các cặp ghép ✓'),
    ('Take a slow, grounding breath and enjoy this restful moment.',
     'Hãy hít một hơi thật sâu, tĩnh tâm và tận hưởng khoảnh khắc thư thái này.'),
    ('>Another round<', '>Chơi ván khác<'),
    ('>Back to games<', '>Về danh sách trò chơi<'),
    ('>Done<', '>Hoàn tất<'),
    ("Hidden card", "Thẻ bài ẩn"),

    # Breathing Setup & Checkpoint
    ('Box Breathing Reset', 'Lấy lại Nhịp điệu với Box Breathing'),
    ('<span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Breathing</span>',
     '<span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Bài tập thở</span>'),
    ('How are you feeling now?', 'Bạn cảm thấy thế nào rồi?'),
    ('Take a breath and check in with your mind and body.',
     'Hít một hơi thở sâu và cảm nhận tâm trí, cơ thể của mình.'),
    ("I'm ready →", 'Tôi đã sẵn sàng →'),
    ('Try something else', 'Thử phương pháp khác'),
    ('Nicely done. Take your grounded energy into your next step.',
     'Làm tốt lắm. Hãy mang nguồn năng lượng bình tâm này vào bước tiếp theo nhé.')
]

for src, rep in replacements:
    text_norm = text_norm.replace(src, rep)

# Re-apply pure CRLF line endings
new_crlf = text_norm.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"stressRelief.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")

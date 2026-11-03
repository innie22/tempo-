import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'communityPosts.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"communityPosts.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')
text_norm = text.replace('\r\n', '\n')

replacements = [
    ('>Like<', '>Thích<'),
    ('>Liked<', '>Đã thích<'),
    ('>Comment<', '>Bình luận<'),
    ('>Share<', '>Chia sẻ<'),
    ('>Save<', '>Lưu<'),
    ('>Saved<', '>Đã lưu<'),
    ('Comments (${commentsCount})', 'Bình luận (${commentsCount})'),
    ('Comments (${post.commentsCount || 0})', 'Bình luận (${post.commentsCount || 0})'),
    ('placeholder="Write a supportive comment..."', 'placeholder="Viết bình luận động viên..."'),
    ('placeholder="Write a comment..."', 'placeholder="Viết bình luận..."'),
    ('>Post Comment<', '>Gửi bình luận<'),
    ('>Post<', '>Đăng bài<'),
    ('>Create Post<', '>Tạo bài viết<'),
    ('>All Posts<', '>Tất cả bài viết<'),
    ('>Latest<', '>Mới nhất<'),
    ('>Popular<', '>Nổi bật<'),
    ('>My Posts<', '>Bài viết của tôi<'),
    ('No posts found', 'Chưa có bài viết nào'),
    ('No comments yet. Be the first to share a kind word!', 'Chưa có bình luận nào. Hãy là người đầu tiên gửi lời động viên nhé!'),
    ('Copied link to post!', 'Đã sao chép liên kết bài viết!'),
    ('Post saved!', 'Đã lưu bài viết!'),
    ('Post removed from saved.', 'Đã bỏ lưu bài viết.')
]

for src, rep in replacements:
    text_norm = text_norm.replace(src, rep)

new_crlf = text_norm.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"communityPosts.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")

def main():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    assert '\r' not in content, 'index.html must have LF line endings!'
    assert '<script src="i18n.js?v=20261101.3"></script>' in content
    assert '<script src="communityPosts.js"></script>' in content
    assert '<script src="mode.js?v=20261101.4"></script>' in content
    content = content.replace('<script src="i18n.js?v=20261101.3"></script>', '<script src="i18n.js?v=20261101.4"></script>')
    content = content.replace('<script src="communityPosts.js"></script>', '<script src="communityPosts.js?v=20261101.1"></script>')
    content = content.replace('<script src="mode.js?v=20261101.4"></script>', '<script src="mode.js?v=20261101.5"></script>')
    assert '\r' not in content
    with open('index.html', 'wb') as f:
        f.write(content.encode('utf-8'))
    print('Successfully bumped versions in index.html with LF line endings!')

if __name__ == '__main__':
    main()

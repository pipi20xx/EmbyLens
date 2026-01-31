let config = { baseUrl: '' };
let currentTab = null;
let currentIcon = "";
let activeType = 'nav'; // 'nav' or 'bookmark'

const addView = document.getElementById('add-view');
const configView = document.getElementById('config-view');
const viewTitle = document.getElementById('view-title');
const toggleBtn = document.getElementById('toggle-config');
const mainTabs = document.getElementById('main-tabs');

// 初始化：读取地址和开关状态
chrome.storage.local.get(['baseUrl', 'appendHome'], (items) => {
    config.baseUrl = items.baseUrl || '';
    document.getElementById('base-url').value = config.baseUrl;
    document.getElementById('append-home').checked = !!items.appendHome;
    
    if (!config.baseUrl) {
        showView('config');
    } else {
        initAddView();
    }
});

function showView(view) {
    if (view === 'config') {
        addView.classList.remove('active');
        configView.classList.add('active');
        mainTabs.style.display = 'none';
        viewTitle.textContent = '助手配置';
    } else {
        configView.classList.remove('active');
        addView.classList.add('active');
        mainTabs.style.display = 'flex';
        viewTitle.textContent = '添加到 Lens';
    }
}

// 标签切换
document.querySelectorAll('.tab').forEach(tab => {
    tab.onclick = () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        activeType = tab.dataset.type;
        
        if (activeType === 'nav') {
            document.getElementById('nav-fields').style.display = 'flex';
            document.getElementById('bookmark-fields').style.display = 'none';
        } else {
            document.getElementById('nav-fields').style.display = 'none';
            document.getElementById('bookmark-fields').style.display = 'flex';
            loadBookmarkFolders();
        }
    };
});

toggleBtn.onclick = () => {
    if (configView.classList.contains('active')) showView('add');
    else showView('config');
};

document.getElementById('back-to-add').onclick = () => showView('add');

document.getElementById('save-config').onclick = () => {
    const baseUrl = document.getElementById('base-url').value.trim().replace(/\/$/, "");
    const appendHome = document.getElementById('append-home').checked;
    
    if (!baseUrl.startsWith('http')) {
        const status = document.getElementById('config-status');
        status.innerHTML = '<span class="error">地址必须以 http:// 开头</span>';
        return;
    }

    chrome.storage.local.set({ baseUrl, appendHome }, () => {
        config.baseUrl = baseUrl;
        const status = document.getElementById('config-status');
        status.innerHTML = '<span class="success">配置已保存</span>';
        setTimeout(() => {
            status.innerHTML = '';
            showView('add');
            initAddView();
        }, 1000);
    });
};

document.getElementById('sync-to-browser').onclick = () => {
    const modal = document.getElementById('confirm-modal');
    modal.style.display = 'flex';

    document.getElementById('modal-cancel').onclick = () => {
        modal.style.display = 'none';
    };

    document.getElementById('modal-confirm').onclick = async () => {
        modal.style.display = 'none';
        await performSync();
    };
};

async function performSync() {
    const btn = document.getElementById('sync-to-browser');
    const status = document.getElementById('config-status');
    
    btn.disabled = true;
    btn.textContent = '正在同步...';

    try {
        // 1. 获取 Lens 书签
        const res = await fetch(`${config.baseUrl}/api/bookmarks/?as_tree=true`);
        const tree = await res.json();

        // 2. 找到浏览器的“书签栏” (通常 ID 为 "1")
        const nodes = await chrome.bookmarks.getTree();
        const root = nodes[0];
        const bookmarkBar = root.children.find(c => c.id === '1' || c.title.includes('书签栏') || c.title.includes('Bookmarks Bar'));

        if (!bookmarkBar) throw new Error('找不到书签栏');

        // 3. 清空现有书签栏内容
        const existing = await chrome.bookmarks.getChildren(bookmarkBar.id);
        for (const item of existing) {
            await chrome.bookmarks.removeTree(item.id);
        }

        // 4. 递归创建新书签
        async function createLocal(lensItems, parentId) {
            for (const item of lensItems) {
                if (item.type === 'folder') {
                    const newFolder = await chrome.bookmarks.create({
                        parentId: parentId,
                        title: item.title
                    });
                    if (item.children) await createLocal(item.children, newFolder.id);
                } else {
                    await chrome.bookmarks.create({
                        parentId: parentId,
                        title: item.title,
                        url: item.url
                    });
                }
            }
        }

        await createLocal(tree, bookmarkBar.id);
        status.innerHTML = '<span class="success">同步成功！书签栏已更新。</span>';
    } catch (err) {
        console.error(err);
        status.innerHTML = `<span class="error">同步失败: ${err.message}</span>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '同步书签到浏览器书签栏';
    }
}

async function initAddView() {
    if (!config.baseUrl) return;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tab;
    document.getElementById('title').value = tab.title;

    // 加载导航分类
    fetch(`${config.baseUrl}/api/navigation/categories`)
        .then(r => r.json())
        .then(cats => {
            const select = document.getElementById('category');
            select.innerHTML = '';
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name;
                select.appendChild(opt);
            });
        })
        .catch(() => {
            document.getElementById('add-status').innerHTML = '<span class="error">连接失败，请检查地址</span>';
        });

    // 获取图标
    fetch(`${config.baseUrl}/api/navigation/fetch-icon?url=${encodeURIComponent(tab.url)}`)
        .then(r => r.json())
        .then(data => {
            currentIcon = data.icon;
            document.getElementById('icon-status').style.display = 'none';
            const img = document.getElementById('icon-img');
            img.src = currentIcon.startsWith('/') ? config.baseUrl + currentIcon : currentIcon;
        });
}

function loadBookmarkFolders() {
    fetch(`${config.baseUrl}/api/bookmarks/?as_tree=true`)
        .then(r => r.json())
        .then(tree => {
            const select = document.getElementById('folder');
            select.innerHTML = '<option value="">根目录</option>';
            
            function traverse(items, level = 0) {
                items.forEach(item => {
                    if (item.type === 'folder') {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = '　'.repeat(level) + '📁 ' + item.title;
                        select.appendChild(opt);
                        if (item.children) traverse(item.children, level + 1);
                    }
                });
            }
            traverse(tree);
        });
}

document.getElementById('save-site').onclick = () => {
    const btn = document.getElementById('save-site');
    btn.disabled = true;
    btn.textContent = '正在保存...';

    if (activeType === 'nav') {
        saveToNavigation(btn);
    } else {
        saveToBookmarks(btn);
    }
};

function saveToNavigation(btn) {
    const payload = {
        title: document.getElementById('title').value,
        url: currentTab.url,
        icon: currentIcon || currentTab.url,
        category_id: parseInt(document.getElementById('category').value) || null,
        description: ""
    };

    fetch(`${config.baseUrl}/api/navigation/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (res.ok) {
            document.getElementById('add-status').innerHTML = '<span class="success">收藏成功！</span>';
            setTimeout(() => window.close(), 1000);
        } else {
            throw new Error('Server error');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.textContent = '确认保存';
        document.getElementById('add-status').innerHTML = '<span class="error">保存失败</span>';
    });
}

function saveToBookmarks(btn) {
    const payload = {
        title: document.getElementById('title').value,
        url: currentTab.url,
        type: 'file',
        icon: currentIcon || currentTab.url,
        parent_id: document.getElementById('folder').value || null,
        order: 0
    };

    fetch(`${config.baseUrl}/api/bookmarks/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (res.ok) {
            document.getElementById('add-status').innerHTML = '<span class="success">书签已添加！</span>';
            setTimeout(() => window.close(), 1000);
        } else {
            throw new Error('Server error');
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.textContent = '确认保存';
        document.getElementById('add-status').innerHTML = '<span class="error">保存失败</span>';
    });
}

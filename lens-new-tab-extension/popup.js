let config = { baseUrl: '' };
let currentTab = null;
let currentIcon = "";

const addView = document.getElementById('add-view');
const configView = document.getElementById('config-view');
const viewTitle = document.getElementById('view-title');
const toggleBtn = document.getElementById('toggle-config');

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
        viewTitle.textContent = '助手配置';
    } else {
        configView.classList.remove('active');
        addView.classList.add('active');
        viewTitle.textContent = '添加到 Lens';
    }
}

toggleBtn.onclick = () => {
    if (configView.classList.contains('active')) showView('add');
    else showView('config');
};

document.getElementById('back-to-add').onclick = () => showView('add');

document.getElementById('save-config').onclick = () => {
    const url = document.getElementById('base-url').value.trim();
    const appendHome = document.getElementById('append-home').checked;

    if (!url.startsWith('http')) {
        alert('地址必须以 http:// 开头');
        return;
    }
    const formattedUrl = url.endsWith('/') ? url.slice(0, -1) : url;
    
    // 同时保存地址和开关
    chrome.storage.local.set({ baseUrl: formattedUrl, appendHome: appendHome }, () => {
        config.baseUrl = formattedUrl;
        document.getElementById('config-status').innerHTML = '<span class="success">配置已保存！</span>';
        setTimeout(() => {
            showView('add');
            initAddView();
        }, 500);
    });
};

async function initAddView() {
    if (!config.baseUrl) return;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tab;
    document.getElementById('title').value = tab.title;

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

    fetch(`${config.baseUrl}/api/navigation/fetch-icon?url=${encodeURIComponent(tab.url)}`)
        .then(r => r.json())
        .then(data => {
            currentIcon = data.icon;
            document.getElementById('icon-status').style.display = 'none';
            const img = document.getElementById('icon-img');
            img.src = currentIcon.startsWith('/') ? config.baseUrl + currentIcon : currentIcon;
        });
}

document.getElementById('save-site').onclick = () => {
    const btn = document.getElementById('save-site');
    btn.disabled = true;
    btn.textContent = '正在保存...';

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
    });
};
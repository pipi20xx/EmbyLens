// 统一使用 local 存储
document.getElementById('save').addEventListener('click', () => {
    const baseUrl = document.getElementById('baseUrl').value.trim().replace(/\/$/, "");
    const appendHome = document.getElementById('appendHome').checked;
    
    if (!baseUrl.startsWith('http')) {
        alert('地址必须以 http:// 开头');
        return;
    }
    chrome.storage.local.set({ baseUrl, appendHome }, () => {
        const status = document.getElementById('status');
        status.textContent = '设置已成功保存到本地！';
        setTimeout(() => { status.textContent = ''; }, 2000);
    });
});

chrome.storage.local.get({ baseUrl: '', appendHome: false }, (items) => {
    document.getElementById('baseUrl').value = items.baseUrl;
    document.getElementById('appendHome').checked = items.appendHome;
});
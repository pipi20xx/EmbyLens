// 瞬间读取存储
chrome.storage.local.get(['baseUrl', 'appendHome'], (items) => {
    let targetUrl = items.baseUrl;
    
    if (targetUrl && targetUrl.startsWith('http')) {
        // 如果开启了自动进入 /home 开关，则在末尾拼接
        if (items.appendHome) {
            targetUrl = targetUrl.endsWith('/') ? targetUrl + 'home' : targetUrl + '/home';
        }

        // 使用 chrome.tabs API 强制更新当前标签页地址
        chrome.tabs.getCurrent((tab) => {
            chrome.tabs.update(tab.id, { url: targetUrl });
        });
    } else {
        document.getElementById('msg').innerHTML = `
            <div style="text-align:center;">
                <p style="color:#ef4444;">未检测到服务器配置</p>
                <button id="go-config" style="padding:8px 16px; background:#2563eb; color:white; border:none; border-radius:4px; cursor:pointer;">去设置地址</button>
            </div>
        `;
        document.getElementById('go-config').onclick = () => {
            // 在 popup 中打开配置视图，或者打开选项页
            chrome.runtime.openOptionsPage();
        };
    }
});
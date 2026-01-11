import sys
import json
import asyncio
import httpx
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QTextEdit, 
                             QLabel, QTabWidget, QGroupBox, QFormLayout, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class TmdbWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, api_key, tmdb_id, m_type):
        super().__init__()
        self.api_key = api_key
        self.tmdb_id = tmdb_id
        self.m_type = m_type
        self.base_url = "https://api.themoviedb.org/3"

    def run(self):
        async def fetch():
            async with httpx.AsyncClient(timeout=15) as client:
                params = {
                    "api_key": self.api_key,
                    "language": "zh-CN",
                    "append_to_response": "alternative_titles,keywords,translations,credits"
                }
                try:
                    url = "{}/{}/{}".format(self.base_url, self.m_type, self.tmdb_id)
                    resp = await client.get(url, params=params)
                    if resp.status_code != 200:
                        return {"error": "HTTP " + str(resp.status_code)}
                    return resp.json()
                except Exception as e:
                    return {"error": str(e)}
        try:
            loop = asyncio.new_event_loop()
            self.finished.emit(loop.run_until_complete(fetch()))
        except Exception as e:
            self.error.emit(str(e))

class TmdbExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMDB 深度数据探测器 (全量对照版)")
        self.resize(1200, 950)
        
        central = QWidget()
        layout = QVBoxLayout(central)

        config = QGroupBox("1. 基础配置")
        cfg_layout = QFormLayout()
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("在此粘贴 TMDB API Key")
        cfg_layout.addRow("API Key:", self.api_key)
        config.setLayout(cfg_layout)
        layout.addWidget(config)

        query = QGroupBox("2. 精准探测")
        q_layout = QHBoxLayout()
        self.type_box = QComboBox()
        self.type_box.addItems(["movie", "tv"])
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("输入 TMDB ID")
        self.btn = QPushButton("开始深度探测")
        self.btn.clicked.connect(self.start)
        q_layout.addWidget(QLabel("类型:"))
        q_layout.addWidget(self.type_box)
        q_layout.addWidget(QLabel("ID:"))
        q_layout.addWidget(self.id_input)
        q_layout.addWidget(self.btn)
        query.setLayout(q_layout)
        layout.addWidget(query)

        self.tabs = QTabWidget()
        self.var_txt = QTextEdit()
        self.title_pool_txt = QTextEdit() 
        self.raw_txt = QTextEdit()
        for txt in [self.var_txt, self.title_pool_txt, self.raw_txt]:
            txt.setReadOnly(True)
            
        self.tabs.addTab(self.var_txt, "二级分类变量 (含对照表)")
        self.tabs.addTab(self.title_pool_txt, "全量标题搜索池")
        self.tabs.addTab(self.raw_txt, "原始完整 JSON")
        layout.addWidget(self.tabs)
        self.setCentralWidget(central)

    def start(self):
        self.btn.setEnabled(False)
        self.worker = TmdbWorker(self.api_key.text().strip(), self.id_input.text().strip(), self.type_box.currentText())
        self.worker.finished.connect(self.done)
        self.worker.error.connect(lambda e: self.done({"error": e}))
        self.worker.start()

    def done(self, data):
        self.btn.setEnabled(True)
        if not data or "error" in data:
            self.var_txt.setText("错误: " + str(data.get("error", "未知错误") if data else "无返回"))
            return

        self.raw_txt.setText(json.dumps(data, indent=4, ensure_ascii=False))
        m_type = self.type_box.currentText()
        
        # 1. 标题
        main_title = data.get('title') or data.get('name') or "未知"
        orig_title = data.get('original_title') or data.get('original_name') or "未知"

        # 2. 制作公司
        companies = data.get('production_companies', [])
        company_info = ["{} ({})".format(c.get('name'), c.get('id')) for c in companies]
        company_ids = [str(c.get('id')) for c in companies]

        # 3. 流派
        genres_list = data.get('genres', [])
        genres_info = ["{} ({})".format(g.get('name'), g.get('id')) for g in genres_list]
        genre_ids = [str(g.get('id')) for g in genres_list]

        # 4. 关键词 (补充对照表)
        kw_data = data.get('keywords', {})
        kw_list = kw_data.get('keywords') or kw_data.get('results') or []
        keywords_info = ["{} ({})".format(k.get('name'), k.get('id')) for k in kw_list]
        kw_ids = [str(k.get('id')) for k in kw_list]

        # 5. 国家语言
        origin_country = data.get('origin_country') or [c.get('iso_3166_1') for c in data.get('production_countries', [])]
        orig_lang = data.get('original_language', '未知')

        # 渲染变量页
        res = "### 精准识别变量与 ID 对照表 ###\n\n"
        res += "标题: " + str(main_title) + "\n"
        res += "原始标题: " + str(orig_title) + "\n"
        res += "原始语言: " + str(orig_lang) + "\n"
        res += "原始地区: " + (", ".join(origin_country) if origin_country else "未知") + "\n\n"
        
        res += "== [A] 分拣核心 IDs (供数据库索引) ==\n"
        res += "流派 IDs: " + ", ".join(genre_ids) + "\n"
        res += "公司 IDs: " + ", ".join(company_ids) + "\n"
        res += "关键词 IDs: " + (", ".join(kw_ids[:15]) + "..." if len(kw_ids)>15 else ", ".join(kw_ids)) + "\n\n"
        
        res += "== [B] 详细名称对照表 (关键分拣参考) ==\n"
        res += "1. 所有流派: " + (", ".join(genres_info) if genres_info else "无") + "\n\n"
        res += "2. 制作公司: " + (", ".join(company_info) if company_info else "无") + "\n\n"
        res += "3. 所有关键词 (Keywords):\n   " + ("\n   ".join(keywords_info) if keywords_info else "无") + "\n\n"
        
        if m_type == 'tv':
            res += "== [C] 播出信息 ==\n"
            res += "首播日期: " + str(data.get('first_air_date', '未知')) + "\n"
            res += "完结日期: " + str(data.get('last_air_date', '进行中')) + "\n"
        else:
            res += "== [C] 上映信息 ==\n"
            res += "上映日期: " + str(data.get('release_date', '未知')) + "\n"
        
        self.var_txt.setText(res)

        # 全量标题汇总
        all_pure_titles = set()
        for t in [main_title, orig_title]: 
            if t and t != "未知": all_pure_titles.add(t)
        alt = data.get('alternative_titles', {})
        alt_list = alt.get('titles') or alt.get('results') or []
        for a in alt_list:
            t = a.get('title') or a.get('name')
            if t: all_pure_titles.add(t)
        trans = data.get('translations', {}).get('translations', [])
        for tr in trans:
            t_data = tr.get('data', {})
            t = t_data.get('title') or t_data.get('name')
            if t: all_pure_titles.add(t)
        
        self.title_pool_txt.setText("### 全量标题池 ({} 个) ###\n\n".format(len(all_pure_titles)) + ", ".join(sorted(list(all_pure_titles))))
        self.tabs.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TmdbExplorer()
    win.show()
    sys.exit(app.exec())
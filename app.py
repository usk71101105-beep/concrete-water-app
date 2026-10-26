import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import streamlit.components.v1 as components

st.set_page_config(
    page_title="生コン単位水量推定試験",
    layout="centered"
)

# カスタムCSS：老眼の方向けに文字を大きくしつつ、1画面に収まるコンパクトな配置を維持
st.markdown("""
<style>
h1 {
    font-size: 26px !important;
    white-space: nowrap !important;
}
h2, h3 {
    font-size: 20px !important;
    white-space: nowrap !important;
}
label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {
    font-size: 16px !important;
    font-weight: bold !important;
    color: #f1f5f9 !important;
}
div[data-testid="stExpander"] details {
    border: 2px solid #3b82f6;
    border-radius: 12px;
    background-color: #1e293b;
    margin-top: 20px;
    margin-bottom: 10px;
}
div[data-testid="stExpander"] summary {
    font-size: 18px !important;
    font-weight: bold !important;
    color: #ffffff !important;
    padding: 12px !important;
}
div[data-testid="stExpander"] summary:hover {
    background-color: #334155;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- 永続化ファイルパス ---
MASTER_FILE = "master_settings.json"
HISTORY_FILE = "history_store.json"

# --- セッション・ローカルストレージ初期化 ---
if "plants" not in st.session_state:
    if os.path.exists(MASTER_FILE):
        try:
            with open(MASTER_FILE, "r", encoding="utf-8") as f:
                m_data = json.load(f)
                st.session_state.plants = m_data.get("plants", [])
                st.session_state.air_meters = m_data.get("air_meters", [])
        except Exception:
            st.session_state.plants = []
            st.session_state.air_meters = []
    if not st.session_state.get("plants"):
        st.session_state.plants = [
            {
                "id": 1,
                "plant_name": "宇部府中",
                "mix_name": "27-12-20-M",
                "w_design": 165.0,
                "c": 300.0,
                "s": 780.0,
                "g": 950.0,
            }
        ]
    if not st.session_state.get("air_meters"):
        st.session_state.air_meters = [
            {
                "id": 1,
                "meter_name": "AM-01 (7L型)",
                "container_volume": 7000.0,
                "total_mass": 4250.0,
                "calibration_date": "2026-04-01"
            }
        ]
    else:
        for m in st.session_state.air_meters:
            if "calibration_date" not in m:
                m["calibration_date"] = "2026-04-01"

if "history" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                st.session_state.history = json.load(f)
        except Exception:
            st.session_state.history = []
    else:
        st.session_state.history = []

if "active_plant_id" not in st.session_state:
    st.session_state.active_plant_id = 1

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "測定"

def save_master():
    data = {
        "plants": st.session_state.plants,
        "air_meters": st.session_state.air_meters
    }
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_history_store():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=4)

# タイトルとサブタイトルの設定
st.title("生コン単位水量推定試験")
st.markdown("##### 土木研究所法〔無注水法〕")

# 選択されているタブの内容を上部に表示
active_tab = st.session_state.current_tab

if active_tab == "測定":
    if not st.session_state.plants or not st.session_state.air_meters:
        st.warning("先に下部のメニューから「プラント」および「メーター」の登録を行ってください。")
    else:
        site_name = st.text_input("現場名", value="〇〇現場")
        project_name = st.text_input("工事件名", value="〇〇道路改良工事")
        
        plant_options = {f"{p['plant_name']} : {p['mix_name']}": p for p in st.session_state.plants}
        
        default_index = 0
        for idx, (k, p) in enumerate(plant_options.items()):
            if p.get('id') == st.session_state.active_plant_id:
                default_index = idx
                break
                
        selected_plant_key = st.selectbox("プラント・配合選択", list(plant_options.keys()), index=default_index, key="measurement_plant_select")
        plant = plant_options[selected_plant_key]
        st.session_state.active_plant_id = plant.get('id')
        
        meter_options = {f"{m['meter_name']} (校正: {m.get('calibration_date', '未設定')})": m for m in st.session_state.air_meters}
        selected_meter_key = st.selectbox("使用エアメーター選択", list(meter_options.keys()))
        meter = meter_options[selected_meter_key]
        
        container_vol = meter['container_volume']
        total_mass = meter['total_mass']

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            measured_mass = st.number_input("容器を含めた測定質量 (g)", value=17500, step=1, format="%d")
        with col_in2:
            measured_air = st.number_input("測定空気量 (%)", value=4.8, step=0.1, format="%.1f")
        bonezai_hosei = 0.0
        
        # --- 自動計算実行 ---
        air_fixed = 4.5
        mass_1m3 = plant['w_design'] + plant['c'] + plant['s'] + plant['g']
        vol_without_air = 1.0 - ((air_fixed + plant['c'] * 0.001) * 0.01)
        unit_vol_mass_mix = mass_1m3 / vol_without_air if vol_without_air > 0 else 0
        sample_air = measured_air - bonezai_hosei
        sample_mass = measured_mass - total_mass
        sample_vol_without_air = container_vol * (1.0 - sample_air * 0.01)
        sample_unit_vol_mass = (sample_mass / sample_vol_without_air) * 1000 if sample_vol_without_air > 0 else 0
        diff_mass = unit_vol_mass_mix - sample_unit_vol_mass
        water_error = diff_mass * 0.7
        estimated_water = plant['w_design'] + water_error
        
        st.subheader("算出結果")
        st.markdown(f"""
        <div style="display: flex; gap: 15px; justify-content: space-around; background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #4f46e5;">
            <div style="flex: 1;">
                <div style="font-size: 20px; color: #d1d5db; font-weight: bold; margin-bottom: 8px;">推定単位水量</div>
                <div style="font-size: 38px; color: #00ffff; font-weight: bold;">{estimated_water:.1f} <span style="font-size: 22px;">kg/m³</span></div>
            </div>
            <div style="flex: 1; border-left: 1px solid #4b5563;">
                <div style="font-size: 20px; color: #d1d5db; font-weight: bold; margin-bottom: 8px;">推定誤差</div>
                <div style="font-size: 38px; color: #ff4b4b; font-weight: bold;">{water_error:+.1f} <span style="font-size: 22px;">kg/m³</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("本日の測定結果を一括保存", type="primary", use_container_width=True):
            record_date_str = datetime.now().strftime("%Y%m%d")
            record_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_record = {
                "日付": record_date_str,
                "日時": record_time,
                "現場名": site_name,
                "工事件名": project_name,
                "プラント": plant['plant_name'],
                "配合": plant['mix_name'],
                "設計単位水量": plant['w_design'],
                "推定単位水量(kg/m3)": round(estimated_water, 1),
                "測定空気量(%)": measured_air
            }
            st.session_state.history.append(new_record)
            save_history_store()
            st.success("保存しました！「履歴」タブからいつでも確認できます。")

elif active_tab == "プラント":
    st.header("プラント配合の選択・切替")
    
    if st.session_state.plants:
        ref_options = {f"{p['plant_name']} : {p['mix_name']} (水:{p['w_design']}kg)": p for p in st.session_state.plants}
        
        default_ref_index = 0
        for idx, (k, p) in enumerate(ref_options.items()):
            if p.get('id') == st.session_state.active_plant_id:
                default_ref_index = idx
                break

        def on_ref_plant_change():
            sel_key = st.session_state.ref_select_dropdown
            chosen = ref_options.get(sel_key)
            if chosen:
                st.session_state.active_plant_id = chosen.get('id')

        selected_ref_key = st.selectbox(
            "今回の測定に反映する配合を選択", 
            list(ref_options.keys()), 
            index=default_ref_index, 
            key="ref_select_dropdown",
            on_change=on_ref_plant_change
        )
        ref_plant = ref_options[selected_ref_key]
        st.session_state.active_plant_id = ref_plant.get('id')
        
        if st.button("選択した配合を今回の測定に反映する", type="primary", use_container_width=True):
            st.session_state.active_plant_id = ref_plant.get('id')
            st.session_state.current_tab = "測定"
            components.html("""
                <script>
                    window.parent.scrollTo({top: 0, behavior: 'instant'});
                    window.scrollTo({top: 0, behavior: 'instant'});
                </script>
            """, height=0)
            st.rerun()

    # 少し間を開ける
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)

    st.header("プラント・配合マスタ登録")
    
    p_name = st.text_input("プラント名", value="宇部府中", key="reg_p_name")
    m_name = st.text_input("配合名", value="27-12-20-M", key="reg_m_name")
        
    st.subheader("配合計画書の数値（1m³当り）")
    w_d = st.number_input("① 水 (kg)", value=165.0, step=0.5, key="reg_w_d")
    c_val = st.number_input("② セメント (kg)", value=300.0, step=1.0, key="reg_c_val")
    s_val = st.number_input("③ 細骨材 合計 (kg)", value=780.0, step=1.0, key="reg_s_val")
    g_val = st.number_input("④ 粗骨材 合計 (kg)", value=950.0, step=1.0, key="reg_g_val")
    
    if st.button("この配合を登録する", type="primary", use_container_width=True):
        new_id = max([p.get('id', 0) for p in st.session_state.plants], default=0) + 1
        st.session_state.plants.append({
            "id": new_id,
            "plant_name": p_name, 
            "mix_name": m_name, 
            "w_design": w_d, 
            "c": c_val, 
            "s": s_val, 
            "g": g_val
        })
        save_master()
        st.success(f"配合「{m_name} ({p_name})」を登録しました！")
        st.rerun()

    if st.session_state.plants:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("登録済み配合の管理（修正・削除）")
        
        for idx, p in enumerate(st.session_state.plants):
            p_id = p.get('id', idx)
            with st.expander(f"【{p['plant_name']}】 {p['mix_name']} (水: {p['w_design']}kg)"):
                with st.form(key=f"edit_plant_form_{p_id}"):
                    edit_p_name = st.text_input("プラント名", value=p['plant_name'], key=f"edit_p_name_{p_id}")
                    edit_m_name = st.text_input("配合名", value=p['mix_name'], key=f"edit_m_name_{p_id}")
                    
                    edit_w_d = st.number_input("① 水 (kg)", value=float(p['w_design']), step=0.5, key=f"edit_w_d_{p_id}")
                    edit_c_val = st.number_input("② セメント (kg)", value=float(p['c']), step=1.0, key=f"edit_c_val_{p_id}")
                    edit_s_val = st.number_input("③ 細骨材 合計 (kg)", value=float(p['s']), step=1.0, key=f"edit_s_val_{p_id}")
                    edit_g_val = st.number_input("④ 粗骨材 合計 (kg)", value=float(p['g']), step=1.0, key=f"edit_g_val_{p_id}")
                    
                    submitted_update = st.form_submit_button("この内容で修正を保存する", type="primary")
                    if submitted_update:
                        st.session_state.plants[idx] = {
                            "id": p_id,
                            "plant_name": edit_p_name,
                            "mix_name": edit_m_name,
                            "w_design": edit_w_d,
                            "c": edit_c_val,
                            "s": edit_s_val,
                            "g": edit_g_val
                        }
                        save_master()
                        st.success("プラント情報を更新しました！")
                        st.rerun()

                if st.button("このプラントを削除する", key=f"del_plant_{p_id}", type="secondary"):
                    st.session_state.plants.pop(idx)
                    save_master()
                    st.warning("プラントを削除しました。")
                    st.rerun()

elif active_tab == "メーター":
    st.header("エアメーター情報登録")
    with st.form("meter_reg"):
        m_name = st.text_input("エアメーター識別名", value="AM-01")
        c_vol = st.number_input("⑩ 下容器容積 (cc)", value=7000.0, step=1.0)
        t_mass = st.number_input("⑪ 蓋を含めた全容器質量 (g)", value=4250.0, step=1.0)
        cal_date = st.date_input("キャリブレーション日（校正日）", value=date.today())
        
        if st.form_submit_button("エアメーターを登録する"):
            new_m_id = max([m.get('id', 0) for m in st.session_state.air_meters], default=0) + 1
            st.session_state.air_meters.append({
                "id": new_m_id,
                "meter_name": m_name, 
                "container_volume": c_vol, 
                "total_mass": t_mass,
                "calibration_date": cal_date.strftime("%Y-%m-%d")
            })
            save_master()
            st.success(f"エアメーター「{m_name}」を登録しました！")
            st.rerun()
            
    if st.session_state.air_meters:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("登録済みエアメーターの管理（修正・削除）")
        
        for idx, m in enumerate(st.session_state.air_meters):
            m_id = m.get('id', idx)
            cal_str = m.get('calibration_date', '未設定')
            with st.expander(f"【{m['meter_name']}】 容積: {m['container_volume']}cc / 質量: {m['total_mass']}g (校正日: {cal_str})"):
                with st.form(key=f"edit_meter_form_{m_id}"):
                    edit_m_name = st.text_input("エアメーター識別名", value=m['meter_name'], key=f"edit_m_name_{m_id}")
                    edit_c_vol = st.number_input("⑩ 下容器容積 (cc)", value=float(m['container_volume']), step=1.0, key=f"edit_c_vol_{m_id}")
                    edit_t_mass = st.number_input("⑪ 蓋を含めた全容器質量 (g)", value=float(m['total_mass']), step=1.0, key=f"edit_t_mass_{m_id}")
                    
                    try:
                        default_cal_dt = datetime.strptime(m.get('calibration_date', '2026-04-01'), "%Y-%m-%d").date()
                    except Exception:
                        default_cal_dt = date.today()
                    
                    edit_cal_date = st.date_input("キャリブレーション日（校正日）", value=default_cal_dt, key=f"edit_cal_date_{m_id}")
                    
                    submitted_meter_update = st.form_submit_button("この内容で修正を保存する", type="primary")
                    if submitted_meter_update:
                        st.session_state.air_meters[idx] = {
                            "id": m_id,
                            "meter_name": edit_m_name,
                            "container_volume": edit_c_vol,
                            "total_mass": edit_t_mass,
                            "calibration_date": edit_cal_date.strftime("%Y-%m-%d")
                        }
                        save_master()
                        st.success("エアメーター情報を更新しました！")
                        st.rerun()

                if st.button("このエアメーターを削除する", key=f"del_meter_{m_id}", type="secondary"):
                    st.session_state.air_meters.pop(idx)
                    save_master()
                    st.warning("エアメーターを削除しました。")
                    st.rerun()

elif active_tab == "履歴":
    st.header("保存済み測定履歴")
    if st.session_state.history:
        for idx, hist in enumerate(st.session_state.history):
            with st.expander(f"{hist['日時']} | {hist['現場名']} ({hist['工事件名']}) [推定水量: {hist['推定単位水量(kg/m3)']}kg/m3]"):
                st.write(f"- **現場名**: {hist['現場名']}")
                st.write(f"- **工事件名**: {hist['工事件名']}")
                st.write(f"- プラント: {hist['プラント']} ({hist['配合']})")
                st.write(f"- 設計単位水量: {hist['設計単位水量']} kg/m³")
                st.write(f"- 測定空気量: {hist['測定空気量(%)']}%")
                
        df_history_export = pd.DataFrame(st.session_state.history)
        csv_data = df_history_export.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="履歴CSVダウンロード",
            data=csv_data,
            file_name=f"concrete_quality_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        if st.button("履歴をすべてクリア"):
            st.session_state.history = []
            save_history_store()
            st.rerun()
    else:
        st.info("保存された履歴はありません。")

elif active_tab == "データ管理":
    st.header("設定データ・測定履歴の保存と読み込み")
    st.markdown("登録したプラント情報や測定履歴データをファイルとして保存したり、復元することができます。")
    
    st.subheader("① プラント・メーター設定の保存（ファイル名カスタム可能）")
    custom_master_name = st.text_input("保存するファイル名 (拡張子.jsonは不要)", value=f"concrete_master_settings_{datetime.now().strftime('%Y%m%d')}")
    master_backup = {
        "plants": st.session_state.plants,
        "air_meters": st.session_state.air_meters
    }
    safe_master_filename = f"{custom_master_name.strip()}.json" if custom_master_name.strip() else f"concrete_master_settings_{datetime.now().strftime('%Y%m%d')}.json"
    st.download_button(
        label="📥 プラント・メーター設定ファイルをダウンロード",
        data=json.dumps(master_backup, ensure_ascii=False, indent=4),
        file_name=safe_master_filename,
        mime="application/json",
        type="primary"
    )
    
    st.markdown("---")
    st.subheader("② 測定履歴データの保存（ファイル名カスタム可能）")
    if st.session_state.history:
        for i, hist in enumerate(st.session_state.history):
            h_date = hist.get("日付", datetime.now().strftime("%Y%m%d"))
            h_site = hist.get("現場名", "現場")
            h_proj = hist.get("工事件名", "工事")
            default_hist_name = f"{h_date}_{h_site}_{h_proj}".replace("/", "_").replace(" ", "_")
            
            custom_hist_name = st.text_input(f"履歴 #{i+1} のファイル名", value=default_hist_name, key=f"cust_hist_name_{i}")
            safe_hist_filename = f"{custom_hist_name.strip()}.json" if custom_hist_name.strip() else f"{default_hist_name}.json"
            
            single_history_json = json.dumps([hist], ensure_ascii=False, indent=4)
            st.download_button(
                label=f"📁 保存: {h_date} / {h_site} ({h_proj})",
                data=single_history_json,
                file_name=safe_hist_filename,
                mime="application/json",
                key=f"dl_hist_{i}"
            )
            st.markdown("---")
    else:
        st.info("保存できる測定履歴がありません。")
        
    st.subheader("③ 保存したデータの読み込み（復元）")
    uploaded_file = st.file_uploader("保存したファイル (.json) を選択", type=["json"], key="restore_uploader")
    if uploaded_file is not None:
        try:
            content = json.load(uploaded_file)
            if isinstance(content, list):
                for rec in content:
                    if rec not in st.session_state.history:
                        st.session_state.history.append(rec)
                save_history_store()
                st.success("測定履歴データを正常に読み込み（復元）しました！「履歴」タブから確認できます。")
            elif isinstance(content, dict) and "plants" in content:
                st.session_state.plants = content["plants"]
                st.session_state.air_meters = content.get("air_meters", [])
                save_master()
                st.success("プラント・メーター設定データを正常に読み込み（復元）しました！")
            else:
                st.error("ファイルの形式が正しくありません。")
        except Exception as e:
            st.error(f"読み込みに失敗しました: {e}")

# ==========================================
# ナビゲーションメニューを一番下に配置 ＆ スクロールトップ処理
# ==========================================
st.markdown("---")
st.markdown("### 📌 メニュー切り替え")
tabs = ["測定", "プラント", "メーター", "履歴", "データ管理"]
selected_tab = st.radio("画面移動", tabs, index=tabs.index(active_tab), horizontal=True, label_visibility="collapsed")

if selected_tab != active_tab:
    st.session_state.current_tab = selected_tab
    components.html("""
        <script>
            function scrollToTop() {
                window.parent.scrollTo({top: 0, behavior: 'instant'});
                window.scrollTo({top: 0, behavior: 'instant'});
                const docEl = window.parent.document.documentElement;
                if (docEl) docEl.scrollTop = 0;
                const body = window.parent.document.body;
                if (body) body.scrollTop = 0;
            }
            scrollToTop();
            setTimeout(scrollToTop, 50);
        </script>
    """, height=0)
    st.rerun()
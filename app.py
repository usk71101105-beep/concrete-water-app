import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

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
label, .stSelectbox label, .stTextInput label, .stNumberInput label {
    font-size: 16px !important;
    font-weight: bold !important;
    color: #f1f5f9 !important;
}
button[data-baseweb="tab"] {
    font-size: 16px !important;
    font-weight: bold !important;
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
                "plant_name": "A工場",
                "mix_name": "24-18-20-N",
                "nominal_strength": "24",
                "slump": 18.0,
                "max_aggregate": 20,
                "concrete_type": "N (普通)",
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
            }
        ]

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

# タブ構成
tab1, tab2, tab3, tab4, tab5 = st.tabs(["測定", "プラント", "メーター", "履歴", "データ管理"])

# ==========================================
# Tab 1: 現場測定（チェックリスト削除版）
# ==========================================
with tab1:
    st.header("現場測定 & 記録入力")
    
    if not st.session_state.plants or not st.session_state.air_meters:
        st.warning("先に「プラント」および「メーター」タブで事前登録を行ってください。（または「データ管理」タブから設定ファイルを読み込んでください）")
    else:
        site_name = st.text_input("現場名", value="〇〇現場")
        project_name = st.text_input("工事件名", value="〇〇道路改良工事")
        
        plant_options = {f"{p['plant_name']} : {p['mix_name']}": p for p in st.session_state.plants}
        
        default_index = 0
        for idx, (k, p) in enumerate(plant_options.items()):
            if p.get('id') == st.session_state.active_plant_id:
                default_index = idx
                break
                
        selected_plant_key = st.selectbox("プラント・配合選択", list(plant_options.keys()), index=default_index)
        plant = plant_options[selected_plant_key]
        st.session_state.active_plant_id = plant.get('id')
        
        meter_options = {m['meter_name']: m for m in st.session_state.air_meters}
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

        if st.button("本日の測定結果を一括保存", type="primary", use_container_width=True):
            record_date_str = datetime.now().strftime("%Y%m%d")
            record_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_record = {
                "日付": record_date_str,
                "日時": record_time,
                "現場名": site_name,
                "工事件名": project_name,
                "種類": plant['concrete_type'],
                "プラント": plant['plant_name'],
                "配合": plant['mix_name'],
                "設計単位水量": plant['w_design'],
                "推定単位水量(kg/m3)": round(estimated_water, 1),
                "測定空気量(%)": measured_air
            }
            st.session_state.history.append(new_record)
            save_history_store()
            st.success("保存しました！再起動しても「履歴」タブや「データ管理」からいつでも確認できます。")

# ==========================================
# Tab 2: プラント・配合登録
# ==========================================
with tab2:
    st.header("プラント・配合マスタ登録（自由入力）")
    with st.form("plant_reg"):
        p_name = st.text_input("プラント名", value="A工場")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            n_str = st.text_input("呼び強度", value="24")
            slump = st.number_input("スランプ (cm)", value=18.0, step=1.0)
        with col_p2:
            max_agg = st.selectbox("粗骨材最大寸法 (mm)", [20, 25, 40])
            
        c_type = st.selectbox("生コンの種類", ["N (普通)", "H (早強)", "M (中庸熱)", "BB (高炉B種)"])
        
        c_code = c_type.split()[0]
        slump_val = int(slump) if slump.is_integer() else slump
        auto_mix_name = f"{n_str}-{slump_val}-{max_agg}-{c_code}"
        
        m_name = st.text_input("配合（自動生成・変更可能）", value=auto_mix_name)
            
        st.subheader("配合計画書の数値（1m³当り）")
        w_d = st.number_input("① 水 (kg)", value=165.0, step=0.5)
        c_val = st.number_input("② セメント (kg)", value=300.0, step=1.0)
        s_val = st.number_input("③ 細骨材 合計 (kg)", value=780.0, step=1.0)
        g_val = st.number_input("④ 粗骨材 合計 (kg)", value=950.0, step=1.0)
        
        if st.form_submit_button("この配合を登録する"):
            new_id = max([p.get('id', 0) for p in st.session_state.plants], default=0) + 1
            st.session_state.plants.append({
                "id": new_id,
                "plant_name": p_name, 
                "mix_name": m_name, 
                "nominal_strength": n_str,
                "slump": slump, 
                "max_aggregate": max_agg, 
                "concrete_type": c_type,
                "w_design": w_d, 
                "c": c_val, 
                "s": s_val, 
                "g": g_val
            })
            save_master()
            st.success(f"配合「{m_name} ({p_name})」を登録しました！")
            
    if st.session_state.plants:
        st.subheader("登録済み配合一覧")
        df_plants = pd.DataFrame(st.session_state.plants)[['concrete_type', 'plant_name', 'mix_name', 'w_design', 'c', 's', 'g']]
        st.dataframe(df_plants, use_container_width=True)
        
        st.subheader("登録済み配合のデータ確認・測定への反映")
        ref_options = {f"{p['plant_name']} : {p['mix_name']} (水:{p['w_design']}kg)": p for p in st.session_state.plants}
        selected_ref_key = st.selectbox("確認・反映する配合を選択", list(ref_options.keys()), key="ref_select_dropdown")
        ref_plant = ref_options[selected_ref_key]
        
        if st.button("この配合を今回の測定に反映する", type="primary"):
            st.session_state.active_plant_id = ref_plant.get('id')
            st.success(f"「{ref_plant['plant_name']} : {ref_plant['mix_name']}」を今回の測定に反映しました！上部の「測定」タブに切り替えてください。")
            
        if st.button("プラント登録をリセット"):
            st.session_state.plants = []
            save_master()
            st.rerun()

# ==========================================
# Tab 3: エアメーター登録
# ==========================================
with tab3:
    st.header("エアメーター情報登録")
    with st.form("meter_reg"):
        m_name = st.text_input("エアメーター識別名", value="AM-01")
        c_vol = st.number_input("⑩ 下容器容積 (cc)", value=7000.0, step=1.0)
        t_mass = st.number_input("⑪ 蓋を含めた全容器質量 (g)", value=4250.0, step=1.0)
        
        if st.form_submit_button("エアメーターを登録する"):
            st.session_state.air_meters.append({
                "id": len(st.session_state.air_meters)+1,
                "meter_name": m_name, 
                "container_volume": c_vol, 
                "total_mass": t_mass
            })
            save_master()
            st.success(f"エアメーター「{m_name}」を登録しました！")
            
    if st.session_state.air_meters:
        st.subheader("登録済みエアメーター一覧")
        st.dataframe(pd.DataFrame(st.session_state.air_meters), use_container_width=True)
        if st.button("エアメーター登録をリセット"):
            st.session_state.air_meters = []
            save_master()
            st.rerun()

# ==========================================
# Tab 4: 履歴確認
# ==========================================
with tab4:
    st.header("保存済み測定履歴")
    if st.session_state.history:
        for idx, hist in enumerate(st.session_state.history):
            with st.expander(f"{hist['日時']} | {hist['現場名']} ({hist['工事件名']}) [推定水量: {hist['推定単位水量(kg/m3)']}kg/m3]"):
                st.write(f"- **現場名**: {hist['現場名']}")
                st.write(f"- **工事件名**: {hist['工事件名']}")
                st.write(f"- **生コン種類**: {hist['種類']} / プラント: {hist['プラント']} ({hist['配合']})")
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

# ==========================================
# Tab 5: データ管理
# ==========================================
with tab5:
    st.header("設定データ・測定履歴の保存と読み込み")
    st.markdown("登録したプラント情報や測定履歴データをファイルとして保存したり、復元することができます。")
    
    master_backup = {
        "plants": st.session_state.plants,
        "air_meters": st.session_state.air_meters
    }
    st.download_button(
        label="① プラント・メーター設定をファイルに保存 (JSON)",
        data=json.dumps(master_backup, ensure_ascii=False, indent=4),
        file_name=f"concrete_master_settings_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )
    
    st.markdown("---")
    st.subheader("② 測定履歴データの保存（ファイル名：日付_現場名_工事件名）")
    if st.session_state.history:
        for i, hist in enumerate(st.session_state.history):
            h_date = hist.get("日付", datetime.now().strftime("%Y%m%d"))
            h_site = hist.get("現場名", "現場")
            h_proj = hist.get("工事件名", "工事")
            safe_filename = f"{h_date}_{h_site}_{h_proj}.json".replace("/", "_").replace(" ", "_")
            
            single_history_json = json.dumps([hist], ensure_ascii=False, indent=4)
            st.download_button(
                label=f"📁 保存: {h_date} / {h_site} ({h_proj})",
                data=single_history_json,
                file_name=safe_filename,
                mime="application/json",
                key=f"dl_hist_{i}"
            )
    else:
        st.info("保存できる測定履歴がありません。")
        
    st.markdown("---")
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
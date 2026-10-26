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

# カスタムCSS：すべてのテキストやボタン、エクスパンダーの文字を確実に白色に設定
st.markdown("""
<style>
/* 全体の背景とレイアウトを画像風のグレーに調整 */
.stApp {
    background-color: #b0b0b0 !important;
}
h1 {
    font-size: 24px !important;
    text-align: center !important;
    color: #000000 !important;
    margin-bottom: 0px !important;
}
/* 土木研究所法の見出しを中央寄せ・白文字に調整 */
.sub-title-center {
    text-align: center !important;
    color: #ffffff !important;
    font-size: 16px !important;
    font-weight: bold !important;
    margin-top: 5px !important;
    margin-bottom: 20px !important;
}
h3, p, label {
    color: #000000 !important;
}
/* 黄色のカスタムボタンおよびすべてのStreamlitボタン内の文字を白に強制 */
.yellow-btn button, .stButton button {
    background-color: #eab308 !important;
    color: #ffffff !important;
    font-weight: bold !important;
    border: none !important;
}
.yellow-btn button *, .stButton button * {
    color: #ffffff !important;
}
.yellow-btn button:hover, .stButton button:hover {
    background-color: #ca8a04 !important;
    color: #ffffff !important;
}
/* エクスパンダー全体のデザインと中の文字をすべて白に強制 */
div[data-testid="stExpander"] details {
    border: 2px solid #3b82f6 !important;
    border-radius: 12px !important;
    background-color: #1e293b !important;
    margin-top: 40px !important;
    margin-bottom: 30px !important;
}
div[data-testid="stExpander"] summary {
    font-size: 18px !important;
    font-weight: bold !important;
    color: #ffffff !important;
    padding: 12px !important;
    background-color: #1e293b !important;
}
div[data-testid="stExpander"] summary * {
    color: #ffffff !important;
}
div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] p,
div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] span,
div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] label {
    color: #ffffff !important;
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
                "plant_name": "中村建材",
                "mix_name": "27-12-20-BB",
                "w_design": 164.0,
                "c": 300.0,
                "s": 780.0,
                "g": 950.0,
            }
        ]
    if not st.session_state.get("air_meters"):
        st.session_state.air_meters = [
            {
                "id": 1,
                "meter_name": "C13-WP776185XT",
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

if "show_exact_result_view" not in st.session_state:
    st.session_state.show_exact_result_view = False

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

active_tab = st.session_state.current_tab

# --- 画像完全一致の結果画面（ワンタップ表示） ---
if st.session_state.show_exact_result_view:
    plant_options = {f"{p['plant_name']} : {p['mix_name']}": p for p in st.session_state.plants}
    plant = plant_options.get(list(plant_options.keys())[0])
    for p in st.session_state.plants:
        if p.get('id') == st.session_state.active_plant_id:
            plant = p
            break
            
    air_fixed = 4.5
    mass_1m3 = plant['w_design'] + plant['c'] + plant['s'] + plant['g']
    vol_without_air = 1.0 - ((air_fixed + plant['c'] * 0.001) * 0.01)
    unit_vol_mass_mix = mass_1m3 / vol_without_air if vol_without_air > 0 else 0
    
    container_vol = st.session_state.get("meas_container_vol", 7000.0)
    total_mass = st.session_state.get("meas_total_mass", 4250.0)
    measured_mass = st.session_state.get("meas_measured_mass", 22875)
    measured_air = st.session_state.get("meas_measured_air", 3.1)
    
    bonezai_hosei = 0.0
    sample_air = measured_air - bonezai_hosei
    sample_mass = measured_mass - total_mass
    sample_vol_without_air = container_vol * (1.0 - sample_air * 0.01)
    sample_unit_vol_mass = (sample_mass / sample_vol_without_air) * 1000 if sample_vol_without_air > 0 else 0
    diff_mass = unit_vol_mass_mix - sample_unit_vol_mass
    water_error = diff_mass * 0.7
    estimated_water = plant['w_design'] + water_error

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            background-color: #b0b0b0;
            margin: 0;
            padding: 5px 10px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            overflow: hidden;
            user-select: none;
        }}
        .container {{
            max-width: 420px;
            margin: 0 auto;
            text-align: center;
        }}
        .title-bar {{
            background-color: #dcdcdc;
            padding: 8px 0;
            font-size: 20px;
            font-weight: bold;
            color: #000000;
            letter-spacing: -0.5px;
            margin-bottom: 2px;
        }}
        .subtitle-bar {{
            font-size: 14px;
            font-weight: bold;
            color: #000000;
            margin-bottom: 12px;
        }}
        .section-label {{
            font-size: 13px;
            font-weight: bold;
            text-align: left;
            color: #000000;
            margin-bottom: 2px;
            padding-left: 2px;
        }}
        .white-box {{
            background-color: #ffffff;
            border-radius: 2px;
            padding: 8px 12px;
            margin-bottom: 10px;
            font-size: 20px;
            font-weight: bold;
            color: #000000;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
        }}
        .result-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 6px 0;
            font-size: 18px;
            font-weight: bold;
        }}
        .label-blue {{
            color: #2563eb;
            font-size: 18px;
        }}
        .val-blue {{
            color: #2563eb;
            font-size: 22px;
        }}
        .unit-blue {{
            color: #2563eb;
            font-size: 18px;
        }}
        .label-black {{
            color: #000000;
            font-size: 18px;
        }}
        .val-black {{
            color: #000000;
            font-size: 22px;
        }}
        .unit-black {{
            color: #000000;
            font-size: 18px;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="title-bar">生コン単位水量推定試験</div>
            <div class="subtitle-bar">（土木研究所法 ［無注水法］ ）</div>

            <div class="section-label">生コン種類</div>
            <div class="white-box">
                <span>{plant['plant_name']}</span>
                <span>{plant['mix_name']}</span>
            </div>

            <div class="section-label">エアメーター番号</div>
            <div class="white-box" style="justify-content: center;">
                <span>{st.session_state.get("meas_meter_name", "C13-WP776185XT")}</span>
            </div>

            <div class="section-label">測定器重量</div>
            <div class="white-box">
                <span>{measured_mass}</span>
                <span style="font-size:16px; font-weight:normal;">g</span>
            </div>

            <div class="section-label">測定エアー量</div>
            <div class="white-box">
                <span>{measured_air:.1f}</span>
                <span style="font-size:16px; font-weight:normal;">%</span>
            </div>

            <div class="result-row">
                <span class="label-blue">推定単位水量</span>
                <span class="val-blue">{round(estimated_water)}</span>
                <span class="unit-blue">kg/m³</span>
            </div>

            <div class="result-row">
                <span class="label-black">配合計画水量</span>
                <span class="val-black">{int(plant['w_design'])}</span>
                <span class="unit-black">kg/m³</span>
            </div>

            <div class="result-row" style="justify-content: flex-end; gap: 45px; margin-top: 4px;">
                <span style="font-size: 22px; font-weight: bold; color: #000000;">{round(estimated_water - plant['w_design'])}</span>
                <span style="font-size: 18px; font-weight: bold; color: #000000;">kg/m³</span>
            </div>
        </div>
    </body>
    </html>
    """, height=490)

    # 戻るボタンと保存ボタンをさらに下へ離す
    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    with st.expander("🛠️ 操作パネル（戻る・結果保存）"):
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("← 入力画面に戻る", use_container_width=True):
                st.session_state.show_exact_result_view = False
                st.rerun()
        with col_b2:
            if st.button("💾 この結果を保存", type="primary", use_container_width=True):
                record_date_str = datetime.now().strftime("%Y%m%d")
                record_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_record = {
                    "日付": record_date_str,
                    "日時": record_time,
                    "現場名": st.session_state.get("meas_site_name", "〇〇現場"),
                    "工事件名": st.session_state.get("meas_project_name", "〇〇工事"),
                    "プラント": plant['plant_name'],
                    "配合": plant['mix_name'],
                    "設計単位水量": plant['w_design'],
                    "推定単位水量(kg/m3)": round(estimated_water, 1),
                    "測定空気量(%)": measured_air
                }
                st.session_state.history.append(new_record)
                save_history_store()
                st.success("保存しました！")

else:
    # --- 通常の入力・操作画面 ---
    st.title("生コン単位水量推定試験")
    st.markdown('<div class="sub-title-center">土木研究所法〔無注水法〕</div>', unsafe_allow_html=True)

    if active_tab == "測定":
        if not st.session_state.plants or not st.session_state.air_meters:
            st.warning("先に下部のメニューから「プラント」および「メーター」の登録を行ってください。")
        else:
            site_name = st.text_input("現場名", value="〇〇現場", key="meas_site_name_input")
            project_name = st.text_input("工事件名", value="〇〇道路改良工事", key="meas_project_name_input")
            
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
            selected_meter_key = st.selectbox("使用エアメーター選択", list(meter_options.keys()), key="measurement_meter_select")
            meter = meter_options[selected_meter_key]
            
            st.session_state.meas_container_vol = meter['container_volume']
            st.session_state.meas_total_mass = meter['total_mass']
            st.session_state.meas_meter_name = meter['meter_name']

            col_in1, col_in2 = st.columns(2)
            with col_in1:
                st.session_state.meas_measured_mass = st.number_input("容器を含めた測定質量 (g)", value=22875, step=1, format="%d", key="meas_mass_input")
            with col_in2:
                st.session_state.meas_measured_air = st.number_input("測定空気量 (%)", value=3.1, step=0.1, format="%.1f", key="meas_air_input")

            # --- 測定質量と空気量の下に小さく結果を表示 ---
            air_fixed_p = 4.5
            mass_1m3_p = plant['w_design'] + plant['c'] + plant['s'] + plant['g']
            vol_without_air_p = 1.0 - ((air_fixed_p + plant['c'] * 0.001) * 0.01)
            unit_vol_mass_mix_p = mass_1m3_p / vol_without_air_p if vol_without_air_p > 0 else 0
            
            c_vol_p = st.session_state.get("meas_container_vol", 7000.0)
            t_mass_p = st.session_state.get("meas_total_mass", 4250.0)
            m_mass_p = st.session_state.get("meas_measured_mass", 22875)
            m_air_p = st.session_state.get("meas_measured_air", 3.1)
            
            sample_air_p = m_air_p
            sample_mass_p = m_mass_p - t_mass_p
            sample_vol_without_air_p = c_vol_p * (1.0 - sample_air_p * 0.01)
            sample_unit_vol_mass_p = (sample_mass_p / sample_vol_without_air_p) * 1000 if sample_vol_without_air_p > 0 else 0
            diff_mass_p = unit_vol_mass_mix_p - sample_unit_vol_mass_p
            water_error_p = diff_mass_p * 0.7
            estimated_water_p = plant['w_design'] + water_error_p
            diff_val_p = round(estimated_water_p - plant['w_design'])

            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 12px; border-radius: 6px; margin: 10px 0; border: 1px solid #cbd5e1;">
                <div style="font-size: 13px; font-weight: bold; color: #334155; margin-bottom: 4px;">📊 簡易計算結果プレビュー</div>
                <div style="display: flex; justify-content: space-around; font-size: 14px; font-weight: bold; color: #0f172a;">
                    <span>推定単位水量: <strong style="color: #2563eb; font-size: 16px;">{round(estimated_water_p)}</strong> kg/m³</span>
                    <span>配合計画水量: <strong>{int(plant['w_design'])}</strong> kg/m³</span>
                    <span>差分: <strong style="color: {'#dc2626' if diff_val_p > 0 else '#2563eb'};">{diff_val_p:+d}</strong> kg/m³</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        st.header("プラント・配合マスタ登録")
        p_name = st.text_input("プラント名", value="中村建材", key="reg_p_name")
        m_name = st.text_input("配合名", value="27-12-20-BB", key="reg_m_name")
        w_d = st.number_input("① 水 (kg)", value=164.0, step=0.5, key="reg_w_d")
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
                        
                        if st.form_submit_button("この内容で修正を保存する", type="primary"):
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
            m_name = st.text_input("エアメーター識別名", value="C13-WP776185XT")
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
                        
                        if st.form_submit_button("この内容で修正を保存する", type="primary"):
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
        st.subheader("① プラント・メーター設定の保存")
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
        st.subheader("② 保存したデータの読み込み（復元）")
        uploaded_file = st.file_uploader("保存したファイル (.json) を選択", type=["json"], key="restore_uploader")
        if uploaded_file is not None:
            try:
                content = json.load(uploaded_file)
                if isinstance(content, list):
                    for rec in content:
                        if rec not in st.session_state.history:
                            st.session_state.history.append(rec)
                    save_history_store()
                    st.success("測定履歴データを正常に読み込みました！")
                elif isinstance(content, dict) and "plants" in content:
                    st.session_state.plants = content["plants"]
                    st.session_state.air_meters = content.get("air_meters", [])
                    save_master()
                    st.success("プラント・メーター設定データを正常に読み込みました！")
                else:
                    st.error("ファイルの形式が正しくありません。")
            except Exception as e:
                st.error(f"読み込みに失敗しました: {e}")

    # ==========================================
    # メニュー切り替えの直前に「単位水量推定結果」ボタンを配置（黄色・文字白）
    # ==========================================
    if active_tab == "測定" and st.session_state.plants and st.session_state.air_meters:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="yellow-btn">', unsafe_allow_html=True)
        if st.button("🌟 単位水量推定結果", use_container_width=True):
            st.session_state.show_exact_result_view = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📌 メニュー切り替え")
    tabs = ["測定", "プラント", "メーター", "履歴", "データ管理"]
    selected_tab = st.radio("画面移動", tabs, index=tabs.index(active_tab), horizontal=True, label_visibility="collapsed")

    if selected_tab != active_tab:
        st.session_state.current_tab = selected_tab
        st.rerun()
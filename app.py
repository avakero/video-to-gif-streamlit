import streamlit as st
import tempfile
import os
from moviepy import VideoFileClip
import numpy as np

# ページ設定: モバイルでの見栄えを良くするためにタイトルとアイコンを設定
st.set_page_config(
    page_title="GIF Maker Mobile",
    page_icon="🎞️",
    layout="centered"
)

def get_file_size_str(file_path):
    """ファイル容量を適切な単位の文字列で返す"""
    if not os.path.exists(file_path):
        return "N/A"
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def main():
    # スタイル調整: モバイルでの余白を最適化
    st.markdown("""
        <style>
        .main { padding-top: 1rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            background-color: #f0f2f6;
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎞️ モバイル GIF 変換")
    
    # 1. ファイルアップロード（一番上に配置）
    uploaded_file = st.file_uploader("動画を選択", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tfile:
            tfile.write(uploaded_file.read())
            temp_video_path = tfile.name

        try:
            clip = VideoFileClip(temp_video_path)
            duration = clip.duration
            width, height = clip.size

            # 元動画情報のサマリー
            st.info(f"📹 {duration:.1f}s | {width}x{height}px")

            # モバイル向けに設定をタブで分割
            tab_time, tab_crop, tab_config = st.tabs(["✂️ 時間", "🖼️ クロップ", "⚙️ 設定"])

            with tab_time:
                st.subheader("再生区間の指定")
                # スライダー1つで開始と終了を直感的に選択
                time_range = st.slider(
                    "作成する範囲 (秒)",
                    0.0, float(duration), (0.0, min(float(duration), 5.0)),
                    step=0.1,
                    format="%.1fs"
                )
                start_time, end_time = time_range

            with tab_crop:
                st.subheader("上下のカット")
                top_crop = st.slider("上から削る (px)", 0, height // 2, 0)
                bottom_crop = st.slider("下から削る (px)", 0, height // 2, 0)
                new_h = height - top_crop - bottom_crop
                
                # クロップ後のプレビューをここに配置（視覚的な確認）
                try:
                    frame_img = clip.get_frame(start_time)
                    cropped_frame = frame_img[top_crop:height-bottom_crop, :]
                    st.image(cropped_frame, caption="切り抜き後のプレビュー", use_container_width=True)
                except:
                    st.caption("プレビューを表示できません")

            with tab_config:
                st.subheader("書き出し詳細")
                resize_factor = st.select_slider(
                    "解像度 (縮小率)",
                    options=[0.1, 0.25, 0.5, 0.75, 1.0],
                    value=0.5,
                    format_func=lambda x: f"{int(x*100)}%"
                )
                fps_value = st.select_slider(
                    "フレームレート (FPS)",
                    options=[5, 8, 10, 12, 15, 20, 24, 30],
                    value=10
                )
                speed_factor = st.slider("再生速度", 0.5, 3.0, 1.0, 0.1, format="%.1fx")

            # 最終確認エリア
            st.divider()
            st.markdown("### 🚀 変換の準備完了")
            status_msg = f"**範囲:** {start_time}s ～ {end_time}s ({end_time - start_time:.1f}s)\n\n" \
                         f"**サイズ:** {int(width*resize_factor)} x {int(new_h*resize_factor)} px"
            st.write(status_msg)

            if st.button("GIFを作成する", type="primary", use_container_width=True):
                process_video(clip, start_time, end_time, resize_factor, speed_factor, fps_value, top_crop, bottom_crop)

        except Exception as e:
            st.error(f"読み込みエラー: {e}")
        finally:
            # 終了処理（動画クリップの解放）
            if 'clip' in locals():
                clip.close()
            # 一時ファイルの削除は変換後に行う必要があるため、ここではパスの管理のみ
    else:
        st.write("動画をアップロードすると編集メニューが表示されます。")

def process_video(clip, start, end, resize, speed, fps, top, bottom):
    """動画処理と書き出しのロジック"""
    output_gif_path = tempfile.mktemp(suffix=".gif")
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("動画を処理中...")
            width, height = clip.size
            
            # 処理チェーン
            processed_clip = (
                clip.subclipped(start, end)
                    .cropped(y1=top, y2=height-bottom)
                    .resized(resize)
                    .with_speed_scaled(speed)
            )

            status_text.text("GIFを生成中... (数秒かかります)")
            progress_bar.progress(50)
            
            # 書き出し
            processed_clip.write_gif(output_gif_path, fps=fps, logger=None)
            
            progress_bar.progress(100)
            status_text.text("完了！")

            file_size = get_file_size_str(output_gif_path)
            st.success(f"✅ 完成！ ({file_size})")
            st.image(output_gif_path, use_container_width=True)

            # ダウンロードボタン
            with open(output_gif_path, "rb") as f:
                st.download_button(
                    label=f"💾 保存する ({file_size})",
                    data=f.read(),
                    file_name="result.gif",
                    mime="image/gif",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"変換エラー: {e}")
        finally:
            if 'processed_clip' in locals():
                processed_clip.close()
            # 生成したGIFを少しの間保持してから削除するか、Streamlitのクリーンアップに任せる

if __name__ == "__main__":
    main()

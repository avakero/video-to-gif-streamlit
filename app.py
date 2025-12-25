import streamlit as st
import tempfile
import os
from moviepy import VideoFileClip
import PIL.Image as Image
import numpy as np

# ページ設定
st.set_page_config(
    page_title="動画 to GIF コンバーター Pro",
    page_icon="🎞️",
    layout="centered"
)

def get_file_size_str(file_path):
    """ファイル容量をKB/MB単位の文字列で返す"""
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def main():
    st.title("🎞️ 動画 GIF 変換アプリ")
    st.markdown("""
    動画をアップロードして、**時間・上下の切り抜き・速度**を調整してGIFを作成できます。
    """)

    # サイドバー: 変換の基本設定
    st.sidebar.header("⚙️ 変換設定")
    resize_factor = st.sidebar.slider("サイズ縮小率 (1.0 = そのまま)", 0.1, 1.0, 0.5, 0.05)
    fps_value = st.sidebar.slider("フレームレート (FPS)", 5, 30, 10)
    speed_factor = st.sidebar.slider("再生速度 (倍速)", 0.5, 5.0, 1.0, 0.1)

    # メイン画面: ファイルアップロード
    uploaded_file = st.file_uploader("動画ファイルをアップロード", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tfile:
            tfile.write(uploaded_file.read())
            temp_video_path = tfile.name

        try:
            clip = VideoFileClip(temp_video_path)
            duration = clip.duration
            width, height = clip.size

            # 元動画の情報を表示
            st.info(f"📹 元動画: {duration:.2f}秒 / {width} x {height} px")

            # 詳細設定エリア
            col_trim, col_crop = st.columns(2)
            
            with col_trim:
                st.subheader("✂️ 時間の指定")
                start_time = st.number_input("開始時間 (秒)", min_value=0.0, max_value=duration, value=0.0, step=0.1)
                end_time = st.number_input("終了時間 (秒)", min_value=0.0, max_value=duration, value=min(duration, 5.0), step=0.1)

            with col_crop:
                st.subheader("🖼️ 上下のカット")
                top_crop = st.slider("上端から削る (px)", 0, height // 2, 0)
                bottom_crop = st.slider("下端から削る (px)", 0, height // 2, 0)
                new_h = height - top_crop - bottom_crop
                st.caption(f"現在の高さ: {new_h} px (縮小後: {int(new_h * resize_factor)} px)")

            # --- 視覚的プレビュー機能 ---
            st.subheader("🔍 設定のプレビュー (静止画)")
            st.write("設定した時間とクロップが適用されたイメージです（枠線を表示しています）")
            
            # 指定した時間のフレームを取得してクロップを適用
            try:
                # 指定秒数のフレームを画像(numpy array)として取得
                frame_img = clip.get_frame(start_time)
                # クロップを画像配列に適用 [y_start:y_end, x_start:x_end]
                cropped_frame = frame_img[top_crop:height-bottom_crop, :]
                
                # Streamlitで表示（枠線をつけるためにCSSを使用するか、そのまま表示）
                # 背景が白い場合に備え、あえて黒い枠線のコンテナに入れる
                st.image(
                    cropped_frame, 
                    caption=f"{start_time}秒時点の切り抜きイメージ",
                    use_container_width=True
                )
                # CSSで画像に外枠をつける（白い背景対策）
                st.markdown(
                    "<style>img { border: 1px solid #ddd; border-radius: 4px; }</style>", 
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning("プレビューの生成に失敗しました。")

            # 入力チェック
            if start_time >= end_time:
                st.error("エラー: 開始時間は終了時間より前に設定してください。")
                return

            # 変換ボタン
            if st.button("🚀 GIF変換を開始する", use_container_width=True):
                if height - top_crop - bottom_crop <= 0:
                    st.error("エラー: 全てをカットすることはできません。")
                else:
                    process_video(clip, start_time, end_time, resize_factor, speed_factor, fps_value, top_crop, bottom_crop)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            if 'clip' in locals():
                clip.close()
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

def process_video(clip, start, end, resize, speed, fps, top, bottom):
    output_gif_path = tempfile.mktemp(suffix=".gif")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("動画を編集しています...")
        progress_bar.progress(25)

        width, height = clip.size
        processed_clip = (
            clip.subclipped(start, end)
                .cropped(y1=top, y2=height-bottom)
                .resized(resize)
                .with_speed_scaled(speed)
        )

        status_text.text("GIFを書き出し中... (時間がかかる場合があります)")
        progress_bar.progress(50)
        processed_clip.write_gif(output_gif_path, fps=fps, logger=None)
        
        progress_bar.progress(100)
        status_text.text("完了！")

        file_size_str = get_file_size_str(output_gif_path)
        st.success(f"✅ 完成！ (容量: {file_size_str})")
        st.image(output_gif_path, caption=f"完成したGIF: {file_size_str}")

        with open(output_gif_path, "rb") as f:
            st.download_button(
                label=f"💾 GIFをダウンロード ({file_size_str})",
                data=f.read(),
                file_name="converted.gif",
                mime="image/gif",
                use_container_width=True
            )

    except Exception as e:
        st.error(f"変換中にエラーが発生しました: {e}")
    finally:
        if 'processed_clip' in locals():
            processed_clip.close()
        if os.path.exists(output_gif_path):
            os.remove(output_gif_path)

if __name__ == "__main__":
    main()

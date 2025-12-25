import streamlit as st
import tempfile
import os
from moviepy import VideoFileClip
import time

# ページ設定
st.set_page_config(
    page_title="動画 to GIF コンバーター Pro",
    page_icon="🎞️",
    layout="centered"
)

def get_file_size_str(file_path):
    """
    ファイルの容量を読みやすい単位(KB/MB)に変換して返す関数
    """
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
    動画をアップロードして、サイズや速度を調整したGIFアニメーションを作成できます。
    """)

    # サイドバー: 変換設定
    st.sidebar.header("⚙️ 変換設定")
    resize_factor = st.sidebar.slider("サイズ縮小率 (1.0 = そのまま)", 0.1, 1.0, 0.5, 0.05)
    fps_value = st.sidebar.slider("フレームレート (FPS)", 5, 30, 10, help="値が高いほど滑らかですが、ファイルサイズが増えます。")
    speed_factor = st.sidebar.slider("再生速度 (倍速)", 0.5, 5.0, 1.0, 0.1)

    st.sidebar.info("💡 **容量を小さくするコツ:**\n- 縮小率を下げる\n- FPSを10〜15にする\n- トリミングで秒数を短くする")

    # ファイルアップロード
    uploaded_file = st.file_uploader("動画ファイルを選択してください", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # 一時ファイルとして動画を保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tfile:
            tfile.write(uploaded_file.read())
            temp_video_path = tfile.name

        try:
            # 動画の読み込み
            clip = VideoFileClip(temp_video_path)
            duration = clip.duration

            st.video(uploaded_file)
            st.info(f"📹 元動画の情報: 長さ {duration:.2f}秒 / サイズ {clip.w}x{clip.h}")

            # トリミング設定
            st.subheader("✂️ 範囲指定")
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.number_input("開始時間 (秒)", min_value=0.0, max_value=duration, value=0.0, step=0.1)
            with col2:
                end_time = st.number_input("終了時間 (秒)", min_value=0.0, max_value=duration, value=min(duration, 5.0), step=0.1)

            if start_time >= end_time:
                st.error("エラー: 開始時間は終了時間より前である必要があります。")
                return

            # 変換実行ボタン
            if st.button("🚀 GIFに変換開始", use_container_width=True):
                process_video(clip, start_time, end_time, resize_factor, speed_factor, fps_value)

        except Exception as e:
            st.error(f"動画の読み込み中にエラーが発生しました: {e}")
        finally:
            # メモリ解放
            if 'clip' in locals():
                clip.close()
            # 動画の一時ファイルを削除
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

def process_video(clip, start, end, resize, speed, fps):
    """
    動画処理とGIF生成を行う関数
    """
    output_gif_path = tempfile.mktemp(suffix=".gif")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("動画を加工中...")
        progress_bar.progress(20)

        # 処理用クリップ作成
        processed_clip = (
            clip.subclipped(start, end)
                .resized(resize)
                .with_speed_scaled(speed)
        )

        status_text.text("GIFファイルを書き出し中... (容量を計算しています)")
        progress_bar.progress(50)
        
        # GIF書き出し
        processed_clip.write_gif(output_gif_path, fps=fps, logger=None)
        
        progress_bar.progress(100)
        status_text.text("変換完了！")

        # ファイル容量の取得
        file_size_str = get_file_size_str(output_gif_path)

        # 結果の表示
        st.success(f"✅ GIFの作成に成功しました！ (ファイル容量: {file_size_str})")
        
        # 容量に応じたアドバイス
        if "MB" in file_size_str and float(file_size_str.split()[0]) > 10.0:
            st.warning("⚠️ ファイルサイズが10MBを超えています。Webサイト等で使用する場合は、設定でサイズやFPSを下げて再試行することをお勧めします。")

        st.image(output_gif_path, caption=f"生成されたGIFプレビュー ({file_size_str})")

        # ダウンロード
        with open(output_gif_path, "rb") as f:
            gif_data = f.read()
            st.download_button(
                label=f"💾 GIFをダウンロード ({file_size_str})",
                data=gif_data,
                file_name="converted_animation.gif",
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

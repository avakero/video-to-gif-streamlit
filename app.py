import streamlit as st
import tempfile
import os
from moviepy import VideoFileClip
import time

# ページ設定: タイトルやアイコン、レイアウトを定義
st.set_page_config(
    page_title="動画 to GIF コンバーター Pro",
    page_icon="🎞️",
    layout="centered"
)

def get_file_size_str(file_path):
    """
    生成されたファイルの容量を計算し、KB/MB単位の文字列で返す関数
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
    動画をアップロードして、**トリミング（時間）**、**クロップ（上下カット）**、**速度**を調整したGIFを作成できます。
    """)

    # サイドバー: 変換の基本設定
    st.sidebar.header("⚙️ 変換設定")
    resize_factor = st.sidebar.slider("サイズ縮小率 (1.0 = そのまま)", 0.1, 1.0, 0.5, 0.05)
    fps_value = st.sidebar.slider("フレームレート (FPS)", 5, 30, 10, help="値が高いほど滑らかですが、容量が増えます。")
    speed_factor = st.sidebar.slider("再生速度 (倍速)", 0.5, 5.0, 1.0, 0.1)

    st.sidebar.info("💡 **容量を抑えるヒント:**\n- 縮小率を0.5以下にする\n- FPSを10〜15にする\n- 不要な上下をカットする")

    # メイン画面: ファイルアップロード
    uploaded_file = st.file_uploader("動画ファイルをアップロード (mp4, mov, avi, mkv)", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        # 動画を一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tfile:
            tfile.write(uploaded_file.read())
            temp_video_path = tfile.name

        try:
            # 動画ファイルを読み込み
            clip = VideoFileClip(temp_video_path)
            duration = clip.duration
            width, height = clip.size

            # 元動画のプレビューと情報を表示
            st.video(uploaded_file)
            st.info(f"📹 元動画: {duration:.2f}秒 / サイズ: {width} x {height}")

            # 詳細設定エリアを2カラムで表示
            col_trim, col_crop = st.columns(2)
            
            with col_trim:
                st.subheader("✂️ 時間の指定")
                start_time = st.number_input("開始時間 (秒)", min_value=0.0, max_value=duration, value=0.0, step=0.1)
                end_time = st.number_input("終了時間 (秒)", min_value=0.0, max_value=duration, value=min(duration, 5.0), step=0.1)

            with col_crop:
                st.subheader("🖼️ 上下のカット")
                top_crop = st.slider("上端から削る (px)", 0, height // 2, 0)
                bottom_crop = st.slider("下端から削る (px)", 0, height // 2, 0)
                st.caption(f"カット後の高さ: {height - top_crop - bottom_crop} px")
                
            # 入力チェック
            if start_time >= end_time:
                st.error("エラー: 開始時間は終了時間より前に設定してください。")
                return

            # 変換ボタン
            if st.button("🚀 GIF変換を開始する", use_container_width=True):
                new_h = height - top_crop - bottom_crop
                if new_h <= 0:
                    st.error("エラー: 全てをカットすることはできません。")
                else:
                    process_video(clip, start_time, end_time, resize_factor, speed_factor, fps_value, top_crop, bottom_crop)

        except Exception as e:
            st.error(f"動画の処理中にエラーが発生しました: {e}")
        finally:
            # メモリ解放と一時ファイルの削除
            if 'clip' in locals():
                clip.close()
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

def process_video(clip, start, end, resize, speed, fps, top, bottom):
    """
    MoviePyを使用して動画を加工し、GIFとして出力する関数
    """
    output_gif_path = tempfile.mktemp(suffix=".gif")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("動画を編集しています...")
        progress_bar.progress(25)

        # 編集の適用 (MoviePy 2.x のメソッド名を使用)
        width, height = clip.size
        processed_clip = (
            clip.subclipped(start, end)           # 時間トリミング
                .cropped(y1=top, y2=height-bottom) # 上下クロップ
                .resized(resize)                  # リサイズ
                .with_speed_scaled(speed)         # 速度変更
        )

        status_text.text("GIFを書き出し中... (これには時間がかかる場合があります)")
        progress_bar.progress(50)
        
        # GIFの保存
        processed_clip.write_gif(output_gif_path, fps=fps, logger=None)
        
        progress_bar.progress(100)
        status_text.text("完了！")

        # 容量の計算
        file_size_str = get_file_size_str(output_gif_path)
        st.success(f"✅ GIFが完成しました！ (ファイル容量: {file_size_str})")
        
        # プレビュー表示
        st.image(output_gif_path, caption=f"プレビュー: {file_size_str}")

        # ダウンロードボタン
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
        # クリップの解放と一時ファイルのクリーンアップ
        if 'processed_clip' in locals():
            processed_clip.close()
        if os.path.exists(output_gif_path):
            os.remove(output_gif_path)

if __name__ == "__main__":
    main()
